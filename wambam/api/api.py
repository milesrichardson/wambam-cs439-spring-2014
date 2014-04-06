import flask
from flask.ext import sqlalchemy
import flask.ext.restless
import flask.ext.login
import uuid
from flask import session, request, redirect, url_for, render_template
from sqlalchemy import create_engine, select

import random
import datetime
import time
import json
import os

import phonenumbers

import login
import schema
import emails
from wambam import app

from pytz import timezone
import pytz
import sqlite3
import uuid

import string

engine = None

def create_app():
    return flask.Flask(__name__)


def create_database(app):
    global engine
    # Create the Flask application and the Flask-SQLAlchemy object    
    app.config["DEBUG"] = True
    using_sqllite = False

    # get the database url from the environment variable
    try:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    except KeyError:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + uuid.uuid1().hex + '.db'
        using_sqllite = True

    
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://adit:@localhost/wambam'

    # sqlite fallback if you don't have postgresql installed

    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    
    # get the database object
    db = sqlalchemy.SQLAlchemy(app)
    schema.create_tables(app, db)

    #update the schema to the current version if necessary
    if using_sqllite or schema.SchemaVersion.query.first().version is not schema.current_schema_version:
        print "Migrating database"
        #need to have a clean session before dropping tables
        db.session.commit()
        db.drop_all()
        db.create_all()
        # Add the version to the database
        version = schema.SchemaVersion(version=schema.current_schema_version)
        db.session.add(version)
        db.session.commit()
    # REMOVE THIS SOON!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        user = schema.Account(
            activated=True,
            phone="770-362-9815",
            phone_carrier="AT&T",
            email="michael.hopkins@yale.edu",
            password_hash="blah",
            online=True,
            first_name="Michael",
            last_name="Hopkins")

        db.session.add(user)
        db.session.commit()

        print 'Done Migrating'
    return db

def create_api(app, db):
    # Create the Flask-Restless API manager.
    manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

    # Create API endpoints, which will be available at /api/<tablename> by
    # default. Allowed HTTP methods can be specified as well.
    
    manager.create_api(schema.Account, methods=['GET', 'POST', 'DELETE', 'PATCH'])
    manager.create_api(schema.Task, methods=['GET', 'POST', 'DELETE'])
    return manager

def add_user(user_data):

    number_object = phonenumbers.parse(user_data["phone"], "US")
    number_formatted = phonenumbers.format_number(number_object, phonenumbers.PhoneNumberFormat.NATIONAL)

    user = schema.Account(
        email_hash=user_data["verification_address"],
        activated=False,
        phone=number_formatted,
        phone_carrier=user_data["phone_carrier"],
        email=user_data["email"],
        password_hash=user_data["pwd"],
        online=True,
        first_name=user_data["first_name"],
        last_name=user_data["last_name"])

    db.session.add(user)
    db.session.commit()

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
    data = flask.jsonify(\
        items=[item.serialize for item in\
               schema.Task.query.filter_by(requestor_id=requestor).all()]
    )
    return data

@app.route('/tasks_for_fulfiller/<int:fulfiller>')
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=[item.serialize for item in data])

# This is unnecessary but Michael requested it ;) <------ :P
@app.route('/get_tasks_as_requestor')
def tasks_as_requestor():
    return tasks_for_requestor(flask.ext.login.current_user.get_id())

@app.route('/get_tasks_as_fulfiller')
def tasks_as_fulfiller():
    return tasks_for_fulfiller(flask.ext.login.current_user.get_id())    


def getTextRecipient(phone_number, phone_carrier):
    emailaddress = phone_number
    emailaddress = emailaddress.replace(" ", "")
    emailaddress = emailaddress.replace("(", "")
    emailaddress = emailaddress.replace(")", "")
    emailaddress = emailaddress.replace("-", "")

    if phone_carrier == "AT&T":
      emailaddress += "@txt.att.net"
    elif phone_carrier == "Boost Mobile":
      emailaddress += "@myboostmobile.com"
    elif phone_carrier == "MetroPCS":
      emailaddress += "@mymetropcs.com"
    elif phone_carrier == "Sprint":
      emailaddress += "@messaging.sprintpcs.com"
    elif phone_carrier == "T-Mobile":
      emailaddress += "@tmomail.net"
    elif phone_carrier == "U.S. Cellular":
      emailaddress += "@email.uscc.net"
    elif phone_carrier == "Virgin Mobile":
      emailaddress += "@vmobl.com"
    else:                                  #else we assume 'Verizon Wirless'
      emailaddress += "@vtext.com"

    return emailaddress

def getPhone(fulfiller):
    return fulfiller.phone

def getPhoneCarrier(fulfiller):
    return fulfiller.phone_carrier

@app.route("/set_online", methods=['POST'])
def set_online():
    app.logger.debug("Start set_online")
    # Get current user
    user = flask.ext.login.current_user
    user_id = int(user.get_id())
    flask_user = schema.Account.query.get(user_id)

    # Set user to be online
    flask_user.online = True;

    # add and commit changes
    db.session.add(flask_user)
    db.session.commit()
    app.logger.debug("End set_online")
    return ""

@app.route("/set_offline", methods=['POST'])
def set_offline():
    app.logger.debug("Start set_offline")
    # Get current user
    user = flask.ext.login.current_user
    user_id = int(user.get_id())
    flask_user = schema.Account.query.get(user_id)

    # Set user to be offline
    flask_user.online = False;

    # add and commit changes
    db.session.add(flask_user)
    db.session.commit()
    app.logger.debug("End set_offline")
    return ""

@app.route("/get_online")
def get_online():
    # Get current user
    user = flask.ext.login.current_user
    user_id = int(user.get_id())
    flask_user = schema.Account.query.get(user_id)

    return flask.jsonify(online=flask_user.online);

@app.route("/submittask", methods=['POST'])
def submit():
    title = request.form['title']
    if not ('lat' in session) or not ('lng' in session):
        app.logger.debug("No lat/lng for task")
        return redirect(url_for('working'))

    lat = float(session['lat'])
    lng = float(session['lng'])
    
    location = request.form['location']
    bid = request.form['bid']
    bid = bid.replace("$","");
    expiration = request.form['expiration']
    description = request.form['description']

    # format for timedelta is (days, seconds, microseconds, 
    # milliseconds, minutes, hours, weeks)
    expirationdate = datetime.datetime.now()
    app.logger.debug(expiration)
    if (expiration == "30min"):
        expirationdate += datetime.timedelta(0,0,0,0,30)
    elif (expiration == "1hr"):
        expirationdate += datetime.timedelta(0,0,0,0,0,1)
        app.logger.debug("1 hour")
    elif (expiration == "1day"):
        expirationdate += datetime.timedelta(1)
    elif (expiration == "1wk"):
        expirationdate += datetime.timedelta(0,0,0,0,0,0,1)

    # Get requestor id 
    current_user = flask.ext.login.current_user
    requestor_id = int(current_user.get_id())

    task = schema.Task(
        requestor_id=requestor_id,
        latitude = lat,
        longitude = lng,
        short_title=title,
        bid=float(bid),
        expiration_datetime=expirationdate,
        long_title=description,
        delivery_location=location,
        status='unassigned')

    db.session.add(task)
    db.session.commit()

    del session['lat']
    del session['lng']

    app.logger.debug('Before confirmation text')    

    # Get logged in user
    user = flask.ext.login.current_user
    user_id = int(user.get_id())
    flask_user = schema.Account.query.get(user_id)
  
    # Get phone info for requester
    phone_number = flask_user.phone
    phone_carrier = flask_user.phone_carrier
    text_recipient = map(getTextRecipient, [phone_number], [phone_carrier])

    # Construct message for requester
    msg_subject = "Order Submitted"
    msg_body = "Your task request for '" + title + " has been placed! We'll text you when someone claims your task."
    app.logger.debug("Email address: " + text_recipient[0])

    # Mail message to requester asynchronously
    emails.send_email(msg_subject, text_recipient, msg_body, msg_body)

    # Send alert text to all online fulfillers 
    # Probably want to do this asynchronously eventually
    fulfillers = schema.Account.query.filter(schema.Account.online == True).all()
    fulfiller_phones = map(getPhone, fulfillers)
    fulfiller_carriers = map(getPhoneCarrier, fulfillers)

    text_fulfillers = map(getTextRecipient, fulfiller_phones, fulfiller_carriers)

    # Remove task requestor from list of potential fulfillers
    if (text_fulfillers.count(text_recipient[0]) > 0):
        text_fulfillers.remove(text_recipient[0])

    # Construct message for potential fulfillers
    msg_subject = "New Task Alert"
    msg_body = flask_user.first_name + " " + flask_user.last_name + " has created a task for '" + title + "'. Click the following link for more details: http://wambam.herokuapp.com/viewtaskdetails/" + str(task.id) + "."

    # Mail message to potential fulfillers
    emails.send_email(msg_subject, text_fulfillers, msg_body, msg_body)

    app.logger.debug("Sent confirmation text")
    app.logger.debug("end submittask")
    return redirect(url_for('confirm'))

def is_session_valid():
    user = flask.ext.login.current_user
    if user.last_request == 0 or 'request_time' not in flask.session or flask.session['request_time'] + 36000000 < user.last_request:
        return False
    return True

@app.before_request
def before_request():
    exempt_files = ['/check_email', '/check_phone', '/favicon.ico',
                    flask.url_for('static', filename='login.css'), 
                    flask.url_for('static', filename='login_mobile.css'),
                    flask.url_for('static', filename='login_validator.js')]

    for f in exempt_files:
        if flask.request.path == f:
            return None

    user = flask.ext.login.current_user

    #trying to access the verification page
    if flask.request.path.startswith('/v/'):
        return None


    #trying to access an unprotected page
    if flask.request.path == '/' or flask.request.path == '/mobile' or \
       flask.request.path == '/login' or flask.request.path == '/register':

        #no need for them to access, go home
        if not user.is_anonymous() and is_session_valid():
            return flask.redirect('/home')
    
    #trying to access a protected page
    else:
        #user is not valid
        if user.is_anonymous() or not is_session_valid():
            if flask.request.path.startswith('/viewtaskdetails/'):
                flask.session['pre_login_url'] = flask.request.path
            return flask.redirect('/')

        else: #session is valid
            #update their token
            user.last_request = int(time.time())
            flask.session['request_time'] = user.last_request
            db.session.commit()
            
            #if they're not activated dont let them go anywhere
            if not is_user_activated() and not (flask.request.path == '/home' or flask.request.path == '/logout' or flask.request.path.endswith('.css') or flask.request.path.endswith('.js')):
                return flask.redirect('/home')

def get_cool_word():
    words = ["Sweet.", "Cool.", "Awesome.", "Dope.", "Word.", "Great.", "Wicked.", "Solid.", "Super.", "Super-duper.", "Excellent.", "Nice."]
    index = random.randint(0, len(words) - 1)
    return words[index]
    
@app.route("/sorry")
def sorry():
    return render_template('alreadyclaimed.html')

@app.route("/claimtask", methods=['POST'])
def claim():
  
    #make task_num equal to the actual number of the task
    task_num = int(request.form['id'])
    task = schema.Task.query.get(task_num)

    if (task.status != "unassigned"):
      return redirect('/sorry')

    title = task.short_title
    location = task.delivery_location
    bid = task.bid
    expiration = schema.dump_datetime(task.expiration_datetime)
    description = task.long_title

    # Get fulfiller
    current_user = flask.ext.login.current_user
    fulfiller_id = int(current_user.get_id())
    fulfiller = schema.Account.query.get(fulfiller_id)


    # Get requester
    current_task = schema.Task.query.get(task_num)
    requestor_id = current_task.requestor_id
    requestor = schema.Account.query.get(requestor_id)
    email = requestor.email

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

    app.logger.debug("Before confirmation text")    

    # Send confirmation text to fulfiller
    fulfiller_number = fulfiller.phone
    fulfiller_carrier = fulfiller.phone_carrier
    text_fulfiller = getTextRecipient(fulfiller_number, fulfiller_carrier)
    app.logger.debug("Email address: " + text_fulfiller)

    # Construct message to send to fulfiller
    msg_subject = "Task Claimed"
    msg_body = "You have claimed the task '" + title + "'. Get in touch with " + requestor.first_name + " " + requestor.last_name + " at " + requestor.phone + "."

    # Send message to fulfiller
    emails.send_email(msg_subject, [text_fulfiller], msg_body, msg_body)

    # Send confirmation text to requestor
    requestor_number = requestor.phone
    requestor_carrier = requestor.phone_carrier
    text_requestor = getTextRecipient(requestor_number, requestor_carrier)
    app.logger.debug("Email address: " + text_requestor)

    # Construct message to send to requestor
    msg_subject = "Your task has been claimed!"
    msg_body = fulfiller.first_name + " " + fulfiller.last_name + " has claimed your task '" + title + "'. You can get in touch with " + fulfiller.first_name + " at " + fulfiller.phone + "."

    # Send confirmation message to requestor
    emails.send_email(msg_subject, [text_requestor], msg_body, msg_body)

    # Get confirmation word
    cool_word = get_cool_word()

    app.logger.debug("Sent confirmation texts")   
    app.logger.debug("end claimtask")
    return render_template('confirmationwambam.html',
                            cool_word = cool_word,
                            title = title,
                            location = location,
                            expiration = expiration,
                            description = description,
                            email = email,
                            bid = "$%(bid).2f" % {"bid": bid},
                            phone= requestor.phone,

                            desktop_client=request.cookies.get('mobile'))

@app.route('/viewtaskdetails/<int:taskid>')
def view_task_details(taskid):
    task = schema.Task.query.filter_by(id=taskid).first()
    if (task is None):
        return flask.redirect('/home')
    else:
        if (task.status != "unassigned"):
          return redirect('/sorry')

        # Get email address of logged in user 
        current_user = flask.ext.login.current_user
        fulfiller_id = int(current_user.get_id())
        fulfiller = schema.Account.query.get(fulfiller_id)

        return render_template('taskview.html',
                                task_id = task.id,
                                lat = task.latitude,
                                lon = task.longitude,
                                title = task.short_title,
                                location = task.delivery_location,
                                bid = "$%(bid).2f" % {"bid": task.bid},
                                expiration = schema.dump_datetime(task.expiration_datetime),
                                description = task.long_title,
                                email = fulfiller.email)


def activate_user(verification_address):
    account = schema.Account.query.filter_by(email_hash=verification_address).first()
    print account
    if account is None:
        return None
    else:
        if account.activated:
            return False
        else:
            account.activated = True
            db.session.commit()
            return True


def is_email_used(email):
    result = schema.Account.query.filter_by(email=email).first() is not None
    return flask.jsonify(used=str(result))

def is_user_activated():
    return flask.ext.login.current_user.activated

app.config['SECRET_KEY'] = str(random.SystemRandom().randint(0,1000000))
app.config['REMEMBER_COOKIE_DURATION'] = datetime.timedelta(days=14)

db = create_database(app)
api_manager = create_api(app,db)
login_manager = login.create_login_manager(app, db)
