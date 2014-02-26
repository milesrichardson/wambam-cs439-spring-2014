import flask
import flask.ext.sqlalchemy
import flask.ext.restless
import uuid

# Create the Flask application and the Flask-SQLAlchemy object.
db_name = uuid.uuid1().hex
app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/' + db_name + '.db'
db = flask.ext.sqlalchemy.SQLAlchemy(app)


account_task = db.Table('account_task',
    db.Column('account_id', db.Integer, db.ForeignKey('account.id')),
    db.Column('task_id', db.Integer, db.ForeignKey('task.id')),
    db.Column('status', db.Enum('active', 'inactive')),
)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20))
    online = db.Column(db.Boolean)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))

    fulfiller_tasks = db.relationship('Task', secondary=account_task,
                            backref=db.backref('acounts', lazy='dynamic'))



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

   

# Create the database tables.
db.create_all()

miles = Account(
    phone="1231231234",
    online=True,
    first_name="Miles",
    last_name="Richardson",
    # tasks=[],
)


will = Account(
    phone="3213214321",
    online=True,
    first_name="Will",
    last_name="CK",
    # tasks=[],
)

task1 = Task(
    requestor_id="5678",
    coordinates="45435345",
    short_title="this",
    long_title="",
    bid=0.0,
    expiration_datetime=None,
    status='expired')

# task2 = Task(
#     id="2234",
#     requestor_id="5678",
#     coordinates="45435345",
#     short_title="this",
#     long_title="",
#     bid=0.0,
#     expiration_datetime=None,
#     status='unassigned',)



db.session.add(task1)
db.session.add(miles)
db.session.add(will)
db.session.commit()


# Create the Flask-Restless API manager.
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.

manager.create_api(Account, methods=['GET', 'POST', 'DELETE'])
manager.create_api(Task, methods=['GET', 'POST', 'DELETE'])

@app.route('/')
def hello():
    return 'Hello World'

@app.route('/tasks_for_requestor/<int:requestor>')
def tasks_for_requestor(requestor):
    response = ''
    return flask.jsonify(items=Task.query.filter_by(requestor_id=requestor).all())

# start the flask loop
app.run()
