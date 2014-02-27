import flask
import flask.ext.sqlalchemy
import flask.ext.restless

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

user_task = None
Account = None
Task = None
app = None

# a join table used for matching the fulfilling users and tasks
def create_account_task_join_table(db):
    global account_task
    account_task = db.Table('account_task',
                         db.Column('account_id', db.Integer, db.ForeignKey('account.id')),
                         db.Column('task_id', db.Integer, db.ForeignKey('task.id')),
                         db.Column('status', db.Enum('active', 'inactive')),  # whether the user is 
                                                                              # assigned to fulfilling this task
                         )
     


def create_account_table(db):
    global Account
    class Account(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        password_hash = db.Column(db.String(255))
        email = db.Column(db.String(255), unique=True)
        phone = db.Column(db.String(20))
        online = db.Column(db.Boolean)
        first_name = db.Column(db.String(255))
        last_name = db.Column(db.String(255))
        
        
        fulfiller_tasks = db.relationship('Task', secondary=account_task,
                                          backref=db.backref('accounts', lazy='dynamic'))

        @property
        def serialize_id(self):
            return {
                'id' : self.id
                }
        
        @property
        def serialize(self):
            return {
               'id' : self.id,
               'phone' : self.phone,
               'online' : self.online,
               'first_name' : self.first_name,
               'last_name' : self.last_name,
               'fulfiller_tasks' : self.serialize_fulfiller_tasks
               }

        @property
        def serialize_fulfiller_tasks(self):
            return [account.serialize_id for account in self.fulfiller_accounts]
        
        def get_auth_token(self):
            s = Serializer(app.config['SECRET_KEY'], expires_in=600)
            token = s.dumps({'id':self.id})
            return token

        @staticmethod
        def verify_auth_token(token):
            s = Serializer(app.config['SECRET_KEY'])
            try:
                data = s.loads(token)
            except SignatureExpired:
                return None
            except BadSignature:
                return None
            return Account.query.get(data['id'])
            

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
            return password == self.password


def create_task_table(db):
    global Task
    class Task(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        requestor_id = db.Column(db.Integer, db.ForeignKey('account.id'))
        coordinates = db.Column(db.String(255))
        short_title = db.Column(db.String(255))
        long_title = db.Column(db.Text)
        bid = db.Column(db.Float())
        expiration_datetime = db.Column(db.DateTime)
        status = db.Column(db.Enum('unassigned', 'in_progress', 'canceled',
                                   'completed', 'expired',
                                   name='task_status_types'))
        
        fulfiller_accounts = db.relationship('Account', secondary=account_task,
                                          backref=db.backref('tasks', lazy='dynamic'))

        @property
        def serialize_id(self):
            return {
                'id' : self.id
                }

        @property
        def serialize(self):
            #Return object data in easily serializeable format
            return {
                'id' : self.id,
                'requestor_id' : self.requestor.id,
                'coordinates' : self.coordinates,
                'short_title' : self.short_title,
                'long_title' : self.long_title,
                'bid' : self.bid,
                'expiration_datetime' : dump_datetime(self.expiration_datetime),
                'status' : self.status,
                'fulfiller_accounts' : self.serialize_fulfiller_accounts
                }

        @property
        def serialize_fulfiller_accounts(self):
            return [account.serialize_id for account in self.fulfiller_accounts]
        

def create_tables(application, db):
    global app
    app = application
    create_account_task_join_table(db)
    create_account_table(db)
    create_task_table(db)
