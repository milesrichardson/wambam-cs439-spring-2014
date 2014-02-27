import flask
import flask.ext.sqlalchemy
import flask.ext.restless
import flask.ext.login
import uuid
from flask import session, request, redirect, url_for

import login
import schema
from wambam import app

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

    michael = schema.Account(
    phone="7703629815",
    email="michael.hopkins@yale.edu",
    online=True,
    first_name="Michael",
    last_name="Hopkins")

    db.session.add(michael)
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

db = create_database(app)
api_manager = create_api(app,db)
login_manager = login.create_login_manager(app)

@app.route('/get_all_active_tasks')
def get_all_active_tasks():
    return flask.jsonify(items=[i.serialize for i in schema.Task.query.filter_by(status='unassigned').all()])

@app.route('/tasks_for_requestor/<int:requestor>')
def tasks_for_requestor(requestor):
    return flask.jsonify(items=schema.Task.query.filter_by(requestor_id=requestor).all())

@app.route('/tasks_for_fulfiller/<int:fulfiller>')
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=data)

@app.route("/submittask", methods=['POST'])
def submit():
    if not ('lat' in session) or not ('lng' in session):
        return redirect(url_for('working'))

    lat = session['lat']
    lng = session['lng']
    title = request.form['title']
    location = request.form['location']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']

    task = schema.Task(
        requestor_id='1',
        coordinates= lat + ',' + lng,
        short_title=title,
        long_title=description,
        bid=float(bid),
        expiration_datetime=None,
        status='unassigned')

    db.session.add(task)
    db.session.commit()
    session.clear()

    app.logger.debug("end submittask")
    return redirect(url_for('confirm'))

@app.route("/claimtask", methods=['POST'])
def claim():

    fulfiller = scheme.Account(
        phone="3213214321",
        online=True,
        first_name="Will",
        last_name="CK")
    task = 1 #request.form['id']

    # add entry to account_task table
    claimed_task = schema.account_task(
        account_id = 1, #fulfiller.id in later versions
        task_id = task,
        status = 'inactive' # inactive immediately for v0
        ) 
    
    # update task table
    temp = schema.Account.query.filter_by(id=int(task)).first()
    temp.status = 'completed'

    # add and commit changes
    db.session.add(claimed_task)
    db.session.commit()

