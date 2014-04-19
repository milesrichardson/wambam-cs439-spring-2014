import flask

from itsdangerous import URLSafeTimedSerializer as Serializer
import datetime

from pytz import timezone
import pytz

from Crypto.Cipher import AES
from base64 import b64encode, b64decode

from wambam import app



current_schema_version = 5

SchemaVersion = None
account_task = None
Account = None
Task = None
Feedback = None
token_serializer = None
token_duration = None
encrypter = None



#a table used to keep track of the version of the schema currently
#stored in the database
def create_schema_version_table(db):
    global SchemaVersion
    class SchemaVersion(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        version = db.Column(db.Integer)


# a join table used for matching the fulfilling users and tasks
def create_account_task_join_table(db):
    global account_task
    account_task = db.Table("account_task",
                         db.Column("account_id", db.Integer, db.ForeignKey("account.id")),
                         db.Column("task_id", db.Integer, db.ForeignKey("task.id")),
                         db.Column("status", db.Enum("active", "inactive", name="status_enum")),  
                         )


def create_account_table(db):
    global Account
    class Account(db.Model):
        encrypted_columns = ["password", "email", "phone", "phone_carrier", "first_name", "last_name"]
        id = db.Column(db.Integer, primary_key=True)
        activated = db.Column(db.Boolean)
        password = db.Column(db.String(255))                #encrypted
        email = db.Column(db.String(255), unique=True)      #encrypted
        email_hash = db.Column(db.String(64), unique=True)
        phone = db.Column(db.String(64), unique=True)       #encrypted
        phone_carrier = db.Column(db.String(255))           #encrypted
        online = db.Column(db.Boolean)
        first_name = db.Column(db.String(255))              #encrypted
        last_name = db.Column(db.String(255))               #encrypted
        last_request = db.Column(db.Integer, default=0)        
        venmo_token = db.Column(db.String(255), default="") #encrypted
        venmo_id = db.Column(db.String(255), default="")    #encrypted
        
        fulfiller_tasks = db.relationship("Task", secondary=account_task,
                                          backref=db.backref("accounts", lazy="dynamic"))

        @property
        def serialize_id(self):
            return {
                "id" : self.id
            }
        
        @property
        def serialize(self):
            return {
               "id" : str(self.id),
               "phone" : decrypt_string(self.phone),
               "phone_carrier" : decrypt_string(self.phone_carrier),
               "online" : str(self.online),
               "first_name" : decrypt_string(self.first_name),
               "last_name" : decrypt_string(self.last_name),
               "fulfiller_tasks" : self.serialize_fulfiller_tasks
            }

        @property
        def serialize_fulfiller_tasks(self):
            return [account.serialize_id for account in self.fulfiller_tasks]
        
        def get_auth_token(self):
            token = token_serializer.dumps([str(self.id), self.password])
            return token

        @staticmethod
        def verify_auth_token(token):
            try:
                data = token_serializer.loads(token, max_age=token_duration)
            except SignatureExpired:
                return None
            except BadSignature:
                return None
            user = Account.query.get(int(data[0]))
        
            if user.verify_password(data[1]): # make sure the passwords match
                return user
            return None

        def is_active(self):
            return True

        def is_anonymous(self):
            return False

        def is_authenticated(self):
            return True
        
        def get_id(self):
            return self.id

        def verify_password(self, password):
            return password == decrypt_string(self.password)

def dump_datetime(value):
    # Deserialize datetime object into string form for JSON processing.
    if value is None:
        return None
    currentTime = datetime.datetime.now()
    delta = value - currentTime
    eastern = timezone("US/Eastern")
    valueEST = (datetime.datetime.now(pytz.utc) + delta).astimezone(eastern)
    # days will be negative if expiration date is in past
    if ((value - currentTime).days < 0):
        return "Passed"
    elif (value.date() == currentTime.date()):
        return valueEST.strftime("%I:%M %p %Z")
    elif ((value.date() - currentTime.date()).days < 7):
        return valueEST.strftime("%A %I:%M %p %Z")
    
    return valueEST.strftime("%B %d, %Y")

def create_task_table(db):
    global Task
    class Task(db.Model):
        encrypted_columns = ["latitude", "longitude", "delivery_location", "short_title", "long_title", "bid"]
        id = db.Column(db.Integer, primary_key=True)
        requestor_id = db.Column(db.Integer, db.ForeignKey("account.id"))
        latitude = db.Column(db.String())                  #encrypted
        longitude = db.Column(db.String())                 #encrypted
        delivery_location = db.Column(db.String(255))      #encrypted
        short_title = db.Column(db.String(255))            #encrypted
        long_title = db.Column(db.String())                #encrypted
        bid = db.Column(db.String())                       #encrypted
        expiration_datetime = db.Column(db.DateTime)
        status = db.Column(db.Enum("unassigned", "in_progress", "canceled",
                                   "completed", "expired",
                                   name="task_status_types"))
        
        fulfiller_accounts = db.relationship("Account", secondary=account_task,
                                            backref=db.backref("tasks", lazy="dynamic"))
        venmo_status = db.Column(db.Enum("paid", "unpaid",\
                                 name="venmo_status"), default="unpaid")


        @property
        def serialize_id(self):
            return {
                "id" : self.id
            }

        @property
        def serialize(self):
            # calculate score to serialize
            num_tasks = len(Feedback.query.filter_by(account_id = self.requestor_id).all())
            num_positive = len(Feedback.query.filter_by(account_id = self.requestor_id, rating = "positive").all())
            if num_tasks == 0:
                score = "this is " + Account.query.get(self.requestor_id).first_name + "'s first post!"
            else:
                score = str(int(num_positive * 100 / num_tasks)) + "%"

            #Return object data in easily serializeable format
            return {
                "id" : str(self.id),
                "requestor_id" : self.requestor_id,
                "requestor_score" : score,
                "requestor_email": self.serialize_requestor_email,
                "latitude" : decrypt_string(self.latitude),
                "longitude" : decrypt_string(self.longitude),
                "delivery_location" : decrypt_string(self.delivery_location),
                "short_title" : decrypt_string(self.short_title),
                "long_title" : decrypt_string(self.long_title),
                "bid" : "$%(bid).2f" % {"bid": float(decrypt_string(self.bid))},
                "expiration_datetime" : dump_datetime(self.expiration_datetime),
                "status" : self.status,
                "fulfiller_accounts" : self.serialize_fulfiller_accounts,
                "venmo_status" : self.venmo_status,
            }

        @property
        def serialize_fulfiller_accounts(self):
            return [account.serialize_id for account in self.fulfiller_accounts]
        
        @property
        def serialize_requestor_email(self):
            return decrypt_string(Account.query.get(self.requestor_id).email)

def create_feedback_table(db):
    global Feedback
    class Feedback(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        task_id = db.Column(db.Integer, db.ForeignKey("task.id"))
        account_id = db.Column(db.Integer, db.ForeignKey("account.id"))
        role = db.Column(db.Enum("fulfiller", "requestor", name="feedback_role"))
        rating = db.Column(db.Enum("positive", "negative",\
                           name="feedback_ratings"), nullable=True)


def create_tables(app, db):
    global token_serializer
    token_serializer = Serializer(app.config["SECRET_KEY"])
    global token_duration
    token_duration = app.config["REMEMBER_COOKIE_DURATION"].total_seconds()
    global encrypter
    encrypter = AES.new(app.config["SECRET_KEY"])

    create_schema_version_table(db)
    create_account_task_join_table(db)
    create_account_table(db)
    create_task_table(db)
    create_feedback_table(db)


def pad_string(raw):
    return raw + (16 - (len(raw)%16)) * ' '

def encrypt_string(plain):
    #add characters until the string has a length multiple of 16
    return plain
#    return b64encode(encrypter.encrypt(pad_string(plain)))

def decrypt_string(enc):
    #remove spaces from end of string
    return enc
"""    try:
        return encrypter.decrypt(b64decode(enc)).rstrip()
    except:
        return enc
"""

def encrypt_dictionary(plaintext):
    keys = plaintext.keys()
    encrypted = {}
    for k in keys:
        if isinstance(plaintext[k], basestring):
            encrypted[k] = encrypt_string(plaintext[k])
        elif isinstance(plaintext[k], float):
            encrypted[k] = encrypt_string(str(plaintext[k]))
    return encrypted

def decrypt_object(encrypted):
    keys = [key for key in dir(encrypted) if not key.startswith('__')]
    plaintext = {}
    for k in keys:
        try:
            value = getattr(encrypted, k)
            if isinstance(value, basestring):
                plaintext[k] = decrypt_string(value)
        except:
            pass
    return plaintext
