import random
import datetime
import time
import json
import os
import uuid
import requests

import flask
from flask import session, request, redirect, url_for, render_template
from flask.ext import sqlalchemy, restless, login as flask_login
from flask_login import current_user
from sqlalchemy import create_engine, select

import phonenumbers

import pytz
from pytz import timezone

import login
import schema
import emails


from wambam import app

#global variable for the flask engine
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
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/' + uuid.uuid1().hex + '.db'
        using_sqllite = True

    
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://adit:@localhost/wambam'

    # sqlite fallback if you don't have postgresql installed

    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    
    # get the database object
    db = sqlalchemy.SQLAlchemy(app)
    schema.create_tables(app, db)

    #update the schema to the current version if necessary
    def initialize_database():
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
            phone="7703629815",
            phone_carrier="AT&T",
            email="michael.hopkins@yale.edu",
            password="blah",
            online=True,
            first_name="Michael",
            last_name="Hopkins")

        task2 = schema.Task(
            requestor_id=1,
            latitude = 41.3121,
            longitude = -72.9277,
            short_title="Title 2",
            bid=float(5),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 2",
            delivery_location="Saybrook",
            status="unassigned")

        task3 = schema.Task(
            requestor_id=1,
            latitude = 41.3101,
            longitude = -72.9257,
            short_title="Title 3",
            bid=float(10),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 3",
            delivery_location="There",
            status="canceled")

        task4 = schema.Task(
            requestor_id=1,
            latitude = 41.3131,
            longitude = -72.9287,
            short_title="Title 4",
            bid=float(15),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 4",
            delivery_location="Here",
            status="expired")

        db.session.add(user)
        db.session.add(task2)
        db.session.add(task3) 
        db.session.add(task4) 
        db.session.commit()
        print "Done Migrating"
    return db

"""
        task1 = schema.Task(
            requestor_id=1,
            latitude = 41.3111,
            longitude = -72.9267,
            short_title="Title 1",
            bid=float(1),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 1",
            delivery_location="CEID",
            status="in_progress")

        task2 = schema.Task(
            requestor_id=1,
            latitude = 41.3121,
            longitude = -72.9277,
            short_title="Title 2",
            bid=float(5),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 2",
            delivery_location="Saybrook",
            status="unassigned")

        task3 = schema.Task(
            requestor_id=1,
            latitude = 41.3101,
            longitude = -72.9257,
            short_title="Title 3",
            bid=float(10),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 3",
            delivery_location="There",
            status="completed")

        task4 = schema.Task(
            requestor_id=1,
            latitude = 41.3131,
            longitude = -72.9287,
            short_title="Title 4",
            bid=float(15),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 4",
            delivery_location="Here",
            status="expired")
"""

def create_api(app, db):
    # Create the Flask-Restless API manager.
    manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

    # Create API endpoints, which will be available at /api/<tablename> by
    # default. Allowed HTTP methods can be specified as well.
    
    # allow clients to get entries and add entries
    manager.create_api(schema.Account, methods=["GET", "POST"])
    manager.create_api(schema.Task, methods=["GET", "POST"])
    manager.create_api(schema.Feedback, methods=["GET", "POST"])
    return manager

def add_user(user_data):

    #format the phone number into a standard format
    number_object = phonenumbers.parse(user_data["phone"], "US")
    number_formatted = phonenumbers.format_number(number_object, phonenumbers.PhoneNumberFormat.NATIONAL)
    user_data["phone"] = number_formatted
    encrypted = schema.encrypt_dictionary(user_data)

    user = schema.Account(
        email_hash=user_data["verification_address"],
        activated=False,
        phone=encrypted["phone"],
        phone_carrier=encrypted["phone_carrier"],
        email=encrypted["email"],
        password=encrypted["pwd"],
        online=True,
        first_name=encrypted["first_name"],
        last_name=encrypted["last_name"])

    db.session.add(user)
    db.session.commit()

#returns json with all of the tasks
@app.route("/get_all_tasks")
def get_all_tasks():
    return flask.jsonify(items=[i.serialize for i in schema.Task.query.all()])

#returns json with all of the tasks that have not been assigned
@app.route("/get_all_active_tasks")
def get_all_active_tasks():
    return flask.jsonify(items=[i.serialize for i in schema.Task.query.filter_by(status="unassigned").all()])

@app.route("/get_all_claimed_tasks")
def get_all_claimed_tasks():
    #I don't think this works, but it's never used
    conn = engine.connect()
    query = select([schema.account_task])
    results = conn.execute(query)

    return flask.jsonify(items=[dict(i) for i in results])

@app.route("/cancel_task/<int:task_id>")
def cancel_task(task_id):
    task = schema.Task.query.get(int(task_id))
    task.status = 'canceled'
    db.session.add(task)
    db.session.commit()
    app.logger.debug("Canceled task with ID %d" % int(task_id))
    return ""

@app.route("/add_feedback")
def add_feedback(methods=["GET"]):
    try:
        task_id = int(request.args.get('task_id'))

        role = request.args.get('role')
        if role not in ['requestor', 'fulfiller']:
            raise Exception('Invalid role')

        rating = request.args.get('rating') 
        if rating not in ['positive', 'negative']:
            raise Exception('Invalid rating')
        
        user_id = int(current_user.get_id())

    except Exception as e:
        print e
        return "error"

    feedback = schema.Feedback(
        task_id = task_id,
        account_id = user_id,
        role = role,
        rating = rating,
    )

    db.session.add(feedback)
    db.session.commit()

    return ""

@app.route("/tasks_for_requestor/<int:requestor>")
def tasks_for_requestor(requestor):
    data = flask.jsonify(\
        items=[item.serialize for item in\
               schema.Task.query.filter_by(requestor_id=requestor).all()]
    )
    return data

@app.route("/tasks_for_fulfiller/<int:fulfiller>")
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=[item.serialize for item in data])

# This is unnecessary but Michael requested it ;)
@app.route("/get_tasks_as_requestor")
def tasks_as_requestor():
    return tasks_for_requestor(current_user.get_id())

@app.route("/get_tasks_as_fulfiller")
def tasks_as_fulfiller():
    return tasks_for_fulfiller(current_user.get_id())    


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
    else:                                  #else we assume Verizon Wirless
        emailaddress += "@vtext.com"

    return emailaddress


@app.route("/set_online", methods=["POST"])
def set_online():
    app.logger.debug("Start set_online")
    # Get current user
    user_id = int(current_user.get_id())
    flask_user = schema.Account.query.get(user_id)

    # Set user to be online
    flask_user.online = True;

    # add and commit changes
    db.session.add(flask_user)
    db.session.commit()
    app.logger.debug("End set_online")
    return ""

@app.route("/set_offline", methods=["POST"])
def set_offline():

    app.logger.debug("Start set_offline")
    # Get current user
    user_id = int(current_user.get_id())
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
    user_id = int(current_user.get_id())
    flask_user = schema.Account.query.get(user_id)

    return flask.jsonify(online=flask_user.online);

@app.route("/submittask", methods=["POST"])
def submit():
    title = request.form["title"]
    if not ("lat" in session) or not ("lng" in session):
        app.logger.debug("No lat/lng for task")
        return redirect(url_for("working"))

    bid = request.form["bid"]
    bid = bid.replace("$","");
    expiration = request.form["expiration"]

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
    requestor_id = int(current_user.get_id())
    
    encrypted = schema.encrypt_dictionary(request.form)
    lat_encrypted = schema.encrypt_string(session["lat"])
    lng_encrypted = schema.encrypt_string(session["lng"])
    bid_encrypted = schema.encrypt_string(bid)

    task = schema.Task(
        requestor_id=requestor_id,
        latitude = lat_encrypted,
        longitude = lng_encrypted,
        short_title=encrypted["title"],
        bid=bid_encrypted,
        expiration_datetime=expirationdate,
        long_title=encrypted["description"],
        delivery_location=encrypted["location"],
        status="unassigned")

    db.session.add(task)
    db.session.commit()

    del session["lat"]
    del session["lng"]


    # Get logged in user
    first_name = schema.decrypt_string(current_user.first_name)
    last_name = schema.decrypt_string(current_user.last_name)

    # Get phone info for requester
    phone_number = schema.decrypt_string(current_user.phone)
    phone_carrier = schema.decrypt_string(current_user.phone_carrier)
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
    def getPhone(fulfiller):
        return schema.decrypt_string(fulfiller.phone)
        
    def getPhoneCarrier(fulfiller):
        return schema.decrypt_string(fulfiller.phone_carrier)

    fulfiller_phones = map(getPhone, fulfillers)
    fulfiller_carriers = map(getPhoneCarrier, fulfillers)

    text_fulfillers = map(getTextRecipient, fulfiller_phones, fulfiller_carriers)

    # Remove task requestor from list of potential fulfillers
    if (text_fulfillers.count(text_recipient[0]) > 0):
        text_fulfillers.remove(text_recipient[0])

    # Construct message for potential fulfillers
    msg_subject = "New Task Alert"
    msg_body = first_name + " " + last_name + " has created a task for '" + title + "'. Click the following link for more details: http://wambam.herokuapp.com/viewtaskdetails/" + str(task.id) + " ."

    # Mail message to potential fulfillers
    emails.send_email(msg_subject, text_fulfillers, msg_body, msg_body)

    app.logger.debug("Sent confirmation text")
    return redirect("/confirm")

def is_session_valid():
    if current_user.last_request == 0 or "request_time" not in session or session["request_time"] + 36000000 < current_user.last_request:
        return False
    return True

@app.before_request
def before_request():
    exempt_files = ["/check_email", "/check_phone", "/favicon.ico",
                    url_for("static", filename="login.css"), 
                    url_for("static", filename="login_mobile.css"),
                    url_for("static", filename="login_validator.js")]

    for f in exempt_files:
        if request.path == f:
            return None

    #trying to access the verification page
    if request.path.startswith("/v/"):
        return None

    #trying to access an unprotected page
    if request.path == "/" or request.path == "/mobile" or \
       request.path == "/login" or request.path == "/register":

        #no need for them to access, go home
        if not current_user.is_anonymous() and is_session_valid():
            return redirect("/home")
    
    #trying to access a protected page
    else:
        #user is not valid
        if current_user.is_anonymous() or not is_session_valid():
            if request.path.startswith("/viewtaskdetails/"):
                session["pre_login_url"] = request.path
            return redirect("/")

        else: #session is valid
            #update their token
            current_user.last_request = int(time.time())
            session["request_time"] = current_user.last_request
            db.session.commit()
            
            #if they"re not activated dont let them go anywhere
            if not current_user.activated and \
               not (request.path == "/home" or request.path == "/logout" or request.path.endswith(".css") or request.path.endswith(".js")):
                return redirect("/home")
                

#used when you've created a task
def get_cool_word():
    words = ["Sweet.", "Cool.", "Awesome.", "Dope.", "Word.", "Great.", "Wicked.", "Solid.", "Super.", "Super-duper.", "Excellent.", "Nice.", "Chill."]
    index = random.randint(0, len(words) - 1)
    return words[index]
    
@app.route("/claimtask", methods=["POST"])
def claim():
  
    #make task_num equal to the actual number of the task
    task_num = int(request.form["id"])
    task = schema.Task.query.get(task_num)

    if (task.status != "unassigned"):
      return redirect("/sorry")

    decrypted_task = schema.decrypt_object(task)
    title = decrypted_task["short_title"]
    location = decrypted_task["delivery_location"]
    bid = float(decrypted_task["bid"])
    expiration = schema.dump_datetime(task.expiration_datetime)
    description = decrypted_task["long_title"]

    # Get fulfiller
    fulfiller = current_user
    decrypted_fulfiller = schema.decrypt_object(fulfiller)

    # Get requester
    current_task = schema.Task.query.get(task_num)
    requestor_id = current_task.requestor_id
    requestor = schema.Account.query.get(requestor_id)
    decrypted_requestor = schema.decrypt_object(requestor)
    email = decrypted_requestor["email"]

    # add entry to account_task table
    conn = engine.connect()
    results = conn.execute(schema.account_task.insert(), 
                           account_id=fulfiller.id, 
                           task_id=task_num, 
                           status="active")
    
    # update task table
    temp = schema.Task.query.get(int(task_num))
    temp.status = "in_progress"

    # commit changes
    # db.session.add(temp)
    db.session.commit()

    app.logger.debug("Before confirmation text")    

    # Send confirmation text to fulfiller
    fulfiller_number = decrypted_fulfiller["phone"]
    fulfiller_carrier = decrypted_fulfiller["phone_carrier"]
    text_fulfiller = getTextRecipient(fulfiller_number, fulfiller_carrier)
    app.logger.debug("Email address: " + text_fulfiller)

    # Construct message to send to fulfiller
    msg_subject = "Task Claimed"
    msg_body = "You have claimed the task '" + title + "'. Get in touch with " + decrypted_requestor["first_name"] + " " + decrypted_requestor["last_name"] + " at " + decrypted_requestor["phone"] + "."

    # Send message to fulfiller
    emails.send_email(msg_subject, [text_fulfiller], msg_body, msg_body)

    # Send confirmation text to requestor
    requestor_number = decrypted_requestor["phone"]
    requestor_carrier = decrypted_requestor["phone_carrier"]
    text_requestor = getTextRecipient(requestor_number, requestor_carrier)
    app.logger.debug("Email address: " + text_requestor)

    # Construct message to send to requestor
    msg_subject = "Your task has been claimed!"
    msg_body = decrypted_fulfiller["first_name"] + " " + decrypted_fulfiller["last_name"] + " has claimed your task '" + title + "'. You can get in touch with " + decrypted_fulfiller["first_name"] + " at " + decrypted_fulfiller["phone"] + "."

    # Send confirmation message to requestor
    emails.send_email(msg_subject, [text_requestor], msg_body, msg_body)

    # Get confirmation word
    cool_word = get_cool_word()

    app.logger.debug("Sent confirmation texts")   
    app.logger.debug("end claimtask")
    return render_template("confirmationwambam.html",
                            cool_word = cool_word,
                            title = title,
                            location = location,
                            expiration = expiration,
                            description = description,
                            email = email,
                            bid = "$%(bid).2f" % {"bid": bid},
                            phone = decrypted_requestor["phone"],
                            desktop_client=request.cookies.get("mobile"))

def create_fulfiller_object(task):
    task_id = task.id
    requester_id = task.requestor_id
    requester = schema.Account.query.get(requester_id)
    requester_email = requester.email
    requester_phone = requester.phone

    expiration_date = schema.dump_datetime(task.expiration_datetime)
    bid = "$%(bid).2f" % {"bid": task.bid}
    app.logger.debug(task.status)
    return {
        'task_id' : task.id,
        'other_email': requester_email,
        'other_phone': requester_phone,
        'expiration_date': expiration_date,
        'bid': bid,
        'lat': task.latitude,
        'lon': task.longitude,
        'delivery_location': task.delivery_location,
        'title': task.short_title,
        'description': task.long_title,
        'status': task.status,
        'venmo_status': task.venmo_status
    }

def create_requester_object(task):
    task_id = task.id
    fulfiller_email = None
    fulfiller_phone = None

    if (task.status == "in_progress" or task.status == "completed"):
        #I am not sure if this is correct...
        fulfiller_id = task.fulfiller_accounts[0].id
        fulfiller = schema.Account.query.get(fulfiller_id)
        fulfiller_email = fulfiller.email
        fulfiller_phone = fulfiller.phone
    
    expiration_date = schema.dump_datetime(task.expiration_datetime)
    bid = "$%(bid).2f" % {"bid": task.bid}
    app.logger.debug(task.status)
    return {
        'task_id' : task.id,
        'other_email': fulfiller_email,
        'other_phone': fulfiller_phone,
        'expiration_date': expiration_date,
        'bid': bid,
        'lat': task.latitude,
        'lon': task.longitude,
        'delivery_location': task.delivery_location,
        'title': task.short_title,
        'description': task.long_title,
        'status': task.status,
        'venmo_status': task.venmo_status
    }

@app.route("/my_requester_tasks")
def my_requester_tasks():
    user_id = flask.ext.login.current_user.get_id()
    tasks_open = schema.Task.query.filter_by(requestor_id=user_id).filter_by(status="unassigned").all()
    tasks_in_progress = schema.Task.query.filter_by(requestor_id=user_id).filter_by(status="in_progress").all()
    tasks_old = schema.Task.query.filter_by(requestor_id=user_id).filter(schema.Task.status!="unassigned").filter(schema.Task.status!="in_progress").all()
    requester_objects_open = map(create_requester_object, tasks_open)
    requester_objects_in_progress = map(create_requester_object, tasks_in_progress)
    requester_objects_old = map(create_requester_object, tasks_old)
    return render_template("tasklist.html",
                            tasks= (requester_objects_open +
                                    requester_objects_in_progress +
                                    requester_objects_old))

def get_task_from_account_task(account_task):
    task_id = account_task.task_id
    task = schema.Task.query.get(task_id)
    return task

@app.route("/my_fulfiller_tasks")
def my_fulfiller_tasks():
    user_id = flask.ext.login.current_user.get_id()

    conn = engine.connect()
    query = select([schema.account_task.c.task_id]).where(schema.account_task.c.account_id == user_id)
    account_tasks = conn.execute(query)

    tasks = map (get_task_from_account_task, account_tasks)
    tasks_in_progress = [elem for elem in tasks if elem.status == "in_progress"]
    tasks_old = [elem for elem in tasks if elem.status != "in_progress"]
    fulfiller_objects_in_progress = map(create_fulfiller_object, tasks_in_progress)
    fulfiller_objects_old = map(create_fulfiller_object, tasks_old)
    return render_template("tasklist.html",
                            tasks= (fulfiller_objects_in_progress +
                                    fulfiller_objects_old))

@app.route("/viewtaskdetails/<int:taskid>")
def view_task_details(taskid):
    task = schema.Task.query.get(taskid)
    task_decrypted = decrypt_object(task)
    if (task is None):
        return redirect("/home")
    else:
        if (task.status != "unassigned"):
          return redirect("/sorry")

        # Get email address of logged in user 
        email = schema.decrypt_string(current_user.email)

        return render_template("taskview.html",
                                task_id = task.id,
                                lat = task_decrypted["latitude"],
                                lon = task_decrypted["longitude"],
                                title = task_decrypted["short_title"],
                                location = task_decrypted["delivery_location"],
                                bid = "$%(bid).2f" % {"bid": task_decrypted["bid"]},
                                expiration = schema.dump_datetime(task.expiration_datetime),
                                description = task_decrypted["long_title"],
                                email = fulfiller.email)


def redirect_to_venmo():
    return redirect("https://api.venmo.com/v1/oauth/authorize?client_id=1687&scope=make_payments%20access_profile&response_type=token")

@app.route("/venmo_auth")
def get_venmo_token():
    token = request.args.get("access_token", None)
    redirect_to = session["post_venmo_url"]
    del session["post_venmo_url"]

    if token is not None:
        current_user.venmo_token = schema.encrypt_string(token)
        db.session.add(current_user)
        db.session.commit()
        return redirect(redirect_to)
    else:
        return redirect("/task_view")

@app.route("/setup_venmo_id")
def setup_venmo_id():
    #get venmo token somehow
    if current_user.venmo_token == "":
        session["post_venmo_url"] = request.path
        return redirect_to_venmo()
        #redirect authenticate to venmo
    else:
        url = "https://api.venmo.com/v1/me?access_token=" + schema.decrypt_string(current_user.venmo_token)
        response = requests.get(url)
        current_user.venmo_token = "";
        response_dict = json.loads(response.text)
        if "error" not in response_dict:
            venmo_id = response_dict["data"]["user"]["id"]
            current_user.venmo_id = schema.encrypt_string(venmo_id)
            db.session.add(current_user)
            db.session.commit()
        return redirect("/task_view")

 
@app.route("/venmo_make_payment")
def make_venmo_payment():
    task_id = int(request.args.get("task_id", None))
    if task_id is None:
        return ""
    task = schema.Task.query.get(task_id)
    if current_user.venmo_token == "":
        session["post_venmo_url"] = request.path
        return redirect_to_venmo()
    else:
        if task.requestor_id is not current_user.id:
            return ""
        #make the payment
        conn = engine.connect()
        query = select([schema.account_task.c.account_id]).where(schema.account_task.c.task_id == task_id)
        fulfiller_account = conn.execute(query)[0]

        data = {
            "access_token":schema.decrypt_string(current_user.venmo_token),
            "user_id":schema.decrypt_string(schema.Account.get(fulfiller_account.account_id).venmo_id)
            "note":"A Wambam! payment for: " + schema.decrypt_string(task.title)
            "amount":schema.decrypt_string(task.bid)
        }
        response = requests.post("https://api.venmo.com/v1/payments", data)
        response_dict = json.loads(response.text)
        if response_dict["data"]["payment"]["status"] == "failed":
            #some shit happened
            pass

        db.session.add(current_user)
        db.session.commit()
        return ""

@app.route("/can_use_venmo")
def can_use_venmo():
    task_id = int(request.args.get("task_id", None))
    if task_id is None:
        return "False"
    task = schema.Task.query.get(task_id)
    conn = engine.connect()
    query = select([schema.account_taks.c.account_id]).where(schema.account_task.c.task_id == task_id)
    fulfiller_account = conn.execute(query)[0]
    
    if schema.Account.get(fulfiller_account.account_id).venmo_id == "":
        return "False"
    return "True"



def activate_user(verification_address):
    account = schema.Account.query.filter_by(email_hash=verification_address).first()
    if account is None:
        return None
    else:
        if account.activated:
            return False
        else:
            account.activated = True
            db.session.add(account)
            db.session.commit()
            return True


def is_email_used(email):
    result = schema.Account.query.filter_by(email=schema.encrypt_string(email)).first() is not None
    return flask.jsonify(used=str(result))

def is_phone_used(phone):
    number_object = phonenumbers.parse(phone, "US")
    number_formatted = phonenumbers.format_number(number_object, phonenumbers.PhoneNumberFormat.NATIONAL)
    result = schema.Account.query.filter_by(phone=schema.encrypt_string(number_formatted)).first() is not None
    return flask.jsonify(used=str(result))

def is_user_activated():
    return current_user.activated

app.config["SECRET_KEY"] = "I have a secret."
app.config["REMEMBER_COOKIE_DURATION"] = datetime.timedelta(days=14)

db = create_database(app)
api_manager = create_api(app,db)
login_manager = login.create_login_manager(app, db)
