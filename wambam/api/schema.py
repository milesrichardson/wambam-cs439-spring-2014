import flask

from itsdangerous import URLSafeTimedSerializer as Serializer
import datetime

from pytz import timezone
import pytz

from wambam import app

current_schema_version = 3

SchemaVersion = None
account_task = None
Account = None
Task = None
Feedback = None
token_serializer = None
token_duration = None

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
        id = db.Column(db.Integer, primary_key=True)
        shit=db.Column(db.Boolean)
        activated = db.Column(db.Boolean)
        password_hash = db.Column(db.String(255))
        email = db.Column(db.String(255), unique=True)
        email_hash = db.Column(db.String(64), unique=True)
        phone = db.Column(db.String(20))
        phone_carrier = db.Column(db.String(255))
        online = db.Column(db.Boolean)
        first_name = db.Column(db.String(255))
        last_name = db.Column(db.String(255))
        last_request = db.Column(db.Integer, default=0)        
        
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
               "id" : self.id,
               "phone" : self.phone,
               "phone_carrier" : self.phone_carrier,
               "online" : self.online,
               "first_name" : self.first_name,
               "last_name" : self.last_name,
               "fulfiller_tasks" : self.serialize_fulfiller_tasks
            }

        @property
        def serialize_fulfiller_tasks(self):
            return [account.serialize_id for account in self.fulfiller_accounts]
        
        def get_auth_token(self):
            token = token_serializer.dumps([str(self.id), self.password_hash])
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

        def hash_password(self, password):
            self.password_hash = custom_app_context.encrypt(password)

        def verify_password(self, password):
            return password == self.password_hash

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
        id = db.Column(db.Integer, primary_key=True)
        requestor_id = db.Column(db.Integer, db.ForeignKey("account.id"))
        latitude = db.Column(db.Float())
        longitude = db.Column(db.Float())
        delivery_location = db.Column(db.String(255))
        short_title = db.Column(db.String(255))
        long_title = db.Column(db.Text)
        bid = db.Column(db.Float())
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
            #Return object data in easily serializeable format
            return {
                "id" : str(self.id),
                "requestor_id" : self.requestor_id,
                "latitude" : str(self.latitude),
                "longitude" : str(self.longitude),
                "delivery_location" : self.delivery_location,
                "short_title" : self.short_title,
                "long_title" : self.long_title,
                "bid" : "$%(bid).2f" % {"bid": self.bid},
                "expiration_datetime" : dump_datetime(self.expiration_datetime),
                "status" : self.status,
                "fulfiller_accounts" : self.serialize_fulfiller_accounts,
                "venmo_status" : self.venmo_status,
            }

        @property
        def serialize_fulfiller_accounts(self):
            return [account.serialize_id for account in self.fulfiller_accounts]
        

def create_feedback_table(db):
    global Feedback
    class Feedback(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        task_id = db.Column(db.Integer, db.ForeignKey("task.id"))
        account_id = db.Column(db.Integer, db.ForeignKey("account.id"))
        role = db.Column(db.Enum("fulfiller", "requestor"))
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

