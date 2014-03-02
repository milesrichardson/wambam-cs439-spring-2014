import flask
import flask.ext.sqlalchemy
import flask.ext.restless
import flask.ext.login
import uuid
from flask import session, request, redirect, url_for, render_template
from sqlalchemy import create_engine, select

import random
import datetime
import time

import login
import schema
from wambam import app

engine = None

def create_app():
    return flask.Flask(__name__)

def create_database(app):
    global engine
    # Create the Flask application and the Flask-SQLAlchemy object
    
    # generate a new name for the database each time, for testing purposes
    db_name = uuid.uuid1().hex

    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/' + db_name + '.db'

    print app.config['SQLALCHEMY_DATABASE_URI']

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    
    # get the database object
    db = flask.ext.sqlalchemy.SQLAlchemy(app)
    schema.create_tables(app, db)

    # Create the database tables.
    db.create_all()

    michael = schema.Account(
    phone="7703629815",
    email="michael.hopkins@yale.edu",
    password_hash="blah",
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

app.config['SECRET_KEY'] = str(random.SystemRandom().randint(0,1000000))
app.config['REMEMBER_COOKIE_DURATION'] = datetime.timedelta(days=14)

db = create_database(app)
api_manager = create_api(app,db)
login_manager = login.create_login_manager(app, db)

@app.route('/get_all_tasks')
def get_all_tasks():
    return flask.jsonify(items=[i.serialize for i in schema.Task.query.all()])

@app.route('/get_all_active_tasks')
def get_all_active_tasks():
    return flask.jsonify(items=[i.serialize for i in schema.Task.query.filter_by(status='unassigned').all()])

@app.route('/get_all_claimed_tasks')
def get_all_claimed_tasks():
    conn = engine.connect()
    query = select([schema.account_task])
    results = conn.execute(query)

    return flask.jsonify(items=[dict(i) for i in results])

@app.route('/tasks_for_requestor/<int:requestor>')
def tasks_for_requestor(requestor):
    return flask.jsonify(items=schema.Task.query.filter_by(requestor_id=requestor).all())

@app.route('/tasks_for_fulfiller/<int:fulfiller>')
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=data)

@app.route("/submittask", methods=['POST'])
def submit():
    title = request.form['title']
    app.logger.debug(title)
    if not ('lat' in session):
        app.logger.debug("hello")
    if not ('lat' in session):
        app.logger.debug("hello2")
    if not ('request_time' in session):
        app.logger.debug('hello3')
    if not ('lat' in session) or not ('lng' in session):
        app.logger.debug("No lat/lng for task")
        return redirect(url_for('working'))

    lat = session['lat']
    lng = session['lng']
    

    location = request.form['location']
    bid = request.form['bid']
    bid = bid.replace("$","");
    expiration = request.form['expiration']
    description = request.form['description']

    task = schema.Task(
        requestor_id='1',
        coordinates= lat + ',' + lng,
        short_title=title,
        bid=float(bid),
        expiration_datetime=None,
        long_title=description,
        status='unassigned')

    db.session.add(task)
    db.session.commit()

    del session['lat']
    del session['lng']

    app.logger.debug("end submittask")
    return redirect(url_for('confirm'))

@app.route("/protected")
def protected():
    return 'Hello World'


def is_session_valid():
    user = flask.ext.login.current_user
    if user.last_request == 0 or 'request_time' not in flask.session or flask.session['request_time'] + 30 < user.last_request:
        return False
    return True

@app.before_request
def before_request():
    user = flask.ext.login.current_user
    if flask.request.path == '/' or flask.request.path == '/login':
        if not user.is_anonymous() and is_session_valid():
            return flask.redirect('/home')

    else:
        if user.is_anonymous() or not is_session_valid():
            return flask.redirect('/')
        else:
            #session is valid
            user.last_request = int(time.time())
            flask.session['request_time'] = user.last_request
            db.session.commit()

    
@app.route("/claimtask", methods=['POST'])
def claim():

    title = request.form['title']
    location = request.form['location']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']
    email = request.form['email']

    fulfiller = schema.Account(
        id=1,
        phone="3213214321",
        online=True,
        first_name="Will",
        last_name="CK")

    #TODO: make task_num equal to the actual number of the task
    task_num = 1 #later on request.form['id']

    # add entry to account_task table
    conn = engine.connect()
    results = conn.execute(schema.account_task.insert(), 
                           account_id=fulfiller.id, 
                           task_id=task_num, 
                           status='inactive')
    
    # update task table
    temp = schema.Task.query.filter_by(id=int(task_num)).first()
    temp.status = 'completed'

    # add and commit changes
    db.session.add(temp)
    db.session.commit()

    app.logger.debug("end claimtask")

    return render_template('confirmationwambam.html',
                            title = request.form['title'],
                            location = request.form['location'],
                            bid = request.form['bid'],
                            expiration = request.form['expiration'],
                            description = request.form['description'],
                            email = request.form['email'],
                            phone="770-362-9815")
