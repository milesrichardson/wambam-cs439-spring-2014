import flask

from itsdangerous import URLSafeTimedSerializer as Serializer
import datetime

from pytz import timezone
import pytz

from wambam import app

import encryption
import venmo

current_schema_version = 7

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

#Table to manage WamBam! accounts. Sensitive information in the table is encrypted
#The encrypted columns are noted in a list below.
def create_account_table(db):
    global Account
    class Account(db.Model):
        encrypted_columns = ["password", "email", "phone",
                             "phone_carrier", "first_name", "last_name"]
        id = db.Column(db.Integer, primary_key=True)
        activated = db.Column(db.Boolean)
        password = db.Column(db.String(360))                #encrypted
        email = db.Column(db.String(360), unique=True)      #encrypted
        email_hash = db.Column(db.String(64), unique=True)
        phone = db.Column(db.String(64), unique=True)       #encrypted
        phone_carrier = db.Column(db.String(360))           #encrypted
        online = db.Column(db.Boolean)
        first_name = db.Column(db.String(360))              #encrypted
        last_name = db.Column(db.String(360))               #encrypted
        last_request = db.Column(db.Integer, default=0)        
        venmo_token = db.Column(db.String(255), default="") #encrypted
        venmo_id = db.Column(db.String(255), default="")    #encrypted
        
        fulfiller_tasks = db.relationship("Task", secondary=account_task,
                                          backref=db.backref("accounts", lazy="dynamic"))

        #Serialize methods for sending data to the frontend.
        @property
        def serialize_id(self):
            return {
                "id" : self.id
            }
        
        @property
        def serialize(self):
            return {
               "id" : str(self.id),
               "phone" : encryption.decrypt_string(self.phone),
               "phone_carrier" : encryption.decrypt_string(self.phone_carrier),
               "online" : str(self.online),
               "email" : encryption.decrypt_string(self.email),
               "first_name" : encryption.decrypt_string(self.first_name),
               "last_name" : encryption.decrypt_string(self.last_name),
               "fulfiller_tasks" : self.serialize_fulfiller_tasks,
               "venmo_token" : str(self.venmo_token)
            }

        @property
        def serialize_fulfiller_tasks(self):
            #we don't want to end up in a recursion where a an account serializes its
            #tasks which in turn serializes accounts associated with it so we just
            #serialize the id here
            return [account.serialize_id for account in self.fulfiller_tasks]
        
        #Methods to ensure that user is properly logged in.
        def get_auth_token(self):
            #return an encrypted token with the id and password hash
            token = token_serializer.dumps([str(self.id), self.password])
            return token

        @staticmethod
        def verify_auth_token(token):
            try:
                #try to load the token, if there is an exception then it is invalid
                #for some reason
                data = token_serializer.loads(token, max_age=token_duration)
            except SignatureExpired:
                return None
            except BadSignature:
                return None
            user = Account.query.get(int(data[0]))
        
            #Make sure the passwords match
            if user.verify_password(data[1]):
                return user
            return None

        #the implementation of the next 4 functions defines a logged in user
        def is_active(self):
            return True

        def is_anonymous(self):
            return False

        def is_authenticated(self):
            return True
        
        def get_id(self):
            return self.id

        def verify_password(self, password):
            return password == encryption.decrypt_string(self.password)

# Serialize datetime object into string form for JSON processing.
def dump_datetime(value):
    if value is None:
        return None
    
    #Ensure time zone is calculated as EST
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

#Table to manage WamBam! tasks. Sensitive information in the table is encrypted
#The encrypted columns are noted in a list below.
def create_task_table(db):
    global Task
    class Task(db.Model):
        encrypted_columns = ["latitude", "longitude", "delivery_location",
                             "short_title", "long_title", "bid"]
        id = db.Column(db.Integer, primary_key=True)
        requestor_id = db.Column(db.Integer, db.ForeignKey("account.id"))
        latitude = db.Column(db.String())                  #encrypted
        longitude = db.Column(db.String())                 #encrypted
        delivery_location = db.Column(db.String(360))      #encrypted
        short_title = db.Column(db.String(360))            #encrypted
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

        #Serialize methods for sending data to the frontend.
        @property
        def serialize_id(self):
            return {
                "id" : self.id
            }

        @property
        def serialize(self):
            # Calculate WamBam! score (c) of requester for a task to serialize
            num_tasks = len(Feedback.query.filter_by(account_id = self.requestor_id).all())
            num_positive = len(Feedback.query.filter_by(account_id = 
                                             self.requestor_id, rating = "positive").all())
            first_name = encryption.decrypt_string(Account.query.get(self.requestor_id).first_name)
            if num_tasks == 0:
                score = first_name + " doesn't have any feedback yet!"
            else:
                score = str(int(num_positive * 100 / num_tasks)) + "%"

            #Return object data in easily serializeable format
            return {
                "id" : str(self.id),
                "requestor_id" : self.requestor_id,
                "requestor_score" : score,
                "requestor_email": self.serialize_requestor_email,
                "latitude" : encryption.decrypt_string(self.latitude),
                "longitude" : encryption.decrypt_string(self.longitude),
                "delivery_location" : encryption.decrypt_string(self.delivery_location),
                "short_title" : encryption.decrypt_string(self.short_title),
                "long_title" : encryption.decrypt_string(self.long_title),
                "bid" : "$%(bid).2f" % {"bid": float(encryption.decrypt_string(self.bid))},
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
            return encryption.decrypt_string(Account.query.get(self.requestor_id).email)

#Feedback table contains information on how fulfiller rates requester in transactions.
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

    create_schema_version_table(db)
    create_account_task_join_table(db)
    create_account_table(db)
    create_task_table(db)
    create_feedback_table(db)

#Method used to gather all information needed for a particular task in the get_fulfiller_tasks
#endpoint.
def create_fulfiller_object(task):
    #For encrypted values of a task, must use task_decrypted.
    task_decrypted = encryption.decrypt_object(task)
    task_id = task.id
    requester_id = task.requestor_id
    requester = Account.query.get(requester_id)
    requester_decrypted = encryption.decrypt_object(requester)
    requester_email = requester_decrypted["email"]
    requester_phone = requester_decrypted["phone"]

    fulfiller_has_venmo = venmo.can_use_venmo(task_id)

    expiration_date = dump_datetime(task.expiration_datetime)
    bid = "$%(bid).2f" % {"bid": float(task_decrypted["bid"])}
    return {
        "object_type": "fulfiller",
        "task_id": task.id,
        "other_email": requester_email,
        "other_phone": requester_phone,
        "expiration_date": expiration_date,
        "bid": bid,
        "lat": task_decrypted["latitude"],
        "lon": task_decrypted["longitude"],
        "delivery_location": task_decrypted["delivery_location"],
        "title": task_decrypted["short_title"],
        "description": task_decrypted["long_title"],
        "fulfiller_has_venmo": fulfiller_has_venmo,
        "status": task.status,
    }

#Method used to gather all information needed for a particular task in the get_requester_tasks
#endpoint.
def create_requester_object(task):
    #For encrypted values of a task, must use task_decrypted.
    task_decrypted = encryption.decrypt_object(task)
    task_id = task.id
    fulfiller_email = None
    fulfiller_phone = None
    fulfiller_has_venmo = "false"

    if (task.status == "in_progress" or task.status == "completed"):
        fulfiller_id = task.fulfiller_accounts[0].id
        fulfiller = Account.query.get(fulfiller_id)
        fulfiller_decrypted = encryption.decrypt_object(fulfiller)
        fulfiller_email = fulfiller_decrypted["email"]
        fulfiller_phone = fulfiller_decrypted["phone"]
        fulfiller_has_venmo = venmo.can_use_venmo(task.id)
    
    expiration_date = dump_datetime(task.expiration_datetime)
    bid = "$%(bid).2f" % {"bid": float(task_decrypted["bid"])}
    return {
        "object_type": "requester",
        "task_id": task.id,
        "other_email": fulfiller_email,
        "other_phone": fulfiller_phone,
        "expiration_date": expiration_date,
        "bid": bid,
        "lat": task_decrypted["latitude"],
        "lon": task_decrypted["longitude"],
        "delivery_location": task_decrypted["delivery_location"],
        "title": task_decrypted["short_title"],
        "description": task_decrypted["long_title"],
        "status": task.status,
        "venmo_status": task.venmo_status,
        "fulfiller_has_venmo": fulfiller_has_venmo
    }
