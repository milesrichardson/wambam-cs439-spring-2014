import flask
import flask.ext.sqlalchemy
import flask.ext.restless
import flask.ext.login
import uuid

import login
import schema

def create_app():
    return flask.Flask(__name__)

def create_database(app):
    # Create the Flask application and the Flask-SQLAlchemy object
    
    # generate a new name for the database each time, for testing purposes
    db_name = uuid.uuid1().hex

    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/' + db_name + '.db'
    
    # get the database object
    db = flask.ext.sqlalchemy.SQLAlchemy(app)
    schema.create_tables(app, db)

    # Create the database tables.
    db.create_all()

    a = schema.Account(email='hihihi', password_hash='')
    db.session.add(a)
    db.session.commit()

    return db


def create_api(app, db):
    # Create the Flask-Restless API manager.
    manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

    # Create API endpoints, which will be available at /api/<tablename> by
    # default. Allowed HTTP methods can be specified as well.
    
    manager.create_api(schema.Account, methods=['GET', 'POST', 'DELETE', 'PATCH'])
    manager.create_api(schema.Task, methods=['GET', 'POST', 'DELETE'])
    return manager


app = create_app()
app.config['SECRET_KEY'] = 'WaMbAm'

db = create_database(app)
api_manager = create_api(app,db)
login_manager = login.create_login_manager(app)

@app.route('/')
@flask.ext.login.login_required
def hello():
    return 'Hello World'

@app.route('/get_all_active_tasks')
def get_all_active_tasks():
    return flask.jsonify(items=schema.Task.query.filter_by(status='unassigned').all())

@app.route('/tasks_for_requestor/<int:requestor>')
def tasks_for_requestor(requestor):
    return flask.jsonify(items=schema.Task.query.filter_by(requestor_id=requestor).all())

@app.route('/tasks_for_fulfiller/<int:fulfiller>')
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=data)

# start the flask loop
app.run()
