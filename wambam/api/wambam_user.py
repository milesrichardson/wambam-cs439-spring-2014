import flask
from flask import session, request, redirect, url_for, render_template
from flask.ext import sqlalchemy, restless, login as flask_login
from flask_login import current_user
from sqlalchemy import create_engine, select, event

import phonenumbers

import schema
import emails
import encryption

db = None
engine = None

#Register all of the endpoints for wambam_user
def setup_user_endpoints(app, database, eng):
    global db
    db = database
    global engine
    engine = eng

    @app.route("/add_feedback/<int:task_id>/<string:rating>", methods=["POST"])
    def feedback_endpoint(task_id, rating):
        return add_feedback(task_id, rating)

    @app.route("/tasks_for_requestor/<int:requestor>")
    def tasks_for_requestor_endpoint(requestor):
        return tasks_for_requestor(requestor)

    @app.route("/tasks_for_fulfiller/<int:fulfiller>")
    def tasks_for_fulfiller_endpoint(fulfiller):
        return tasks_for_fulfiller(fulfiller)

    @app.route("/get_tasks_as_requestor")
    def tasks_as_requestor():
        return tasks_for_requestor(current_user.get_id())

    @app.route("/get_tasks_as_fulfiller")
    def tasks_as_fulfiller():
        return tasks_for_fulfiller(current_user.get_id())

    @app.route("/get_user")
    def get_user():
        if not current_user.is_authenticated():
            return flask.jsonify([])
        return flask.jsonify(current_user.serialize)

    @app.route("/set_online", methods=["POST"])
    def set_online_endpoint():
        return set_online()

    @app.route("/set_offline", methods=["POST"])
    def set_offline_endpoint():
        return set_offline()

    @app.route("/get_online")
    def get_online():
        #Get current user
        user_id = int(current_user.get_id())
        flask_user = schema.Account.query.get(user_id)
        return flask.jsonify(online=flask_user.online);

    @app.route("/my_requester_tasks")
    def my_requester_tasks_endpoint():
        return my_requester_tasks()

    @app.route("/my_fulfiller_tasks")
    def my_fulfiller_tasks_endpoint():
        return my_fulfiller_tasks()

#Create an account for a new user.
def add_user(user_data):
    #Format the phone number into a standard format
    number_object = phonenumbers.parse(user_data["phone"], "US")
    number_formatted = phonenumbers.format_number(
                          number_object, phonenumbers.PhoneNumberFormat.NATIONAL)
    user_data["phone"] = number_formatted
    encrypted = encryption.encrypt_dictionary(user_data)

    #Create user object
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

#Allow fulfiller to submit feedback data on a requester for a task that they have engaged in.
def add_feedback(task_id, rating):
    #Verify rating is valid and determine if user is a requester or fulfiller.
    try:
        task = schema.Task.query.get(int(task_id))

        if rating not in ['positive', 'negative']:
            app.logger.debug("RATING: " + rating)
            raise Exception('Invalid rating')
        
        user_id = int(current_user.get_id())

        if user_id == task.requestor_id:
            role = "requestor"
        else:
            role = "fulfiller"

    except Exception as e:
        return "error"

    #Only add entry in feedback table if task is still in_progress
    if task.status == "in_progress":
        feedback = schema.Feedback(
            task_id = task_id,
            account_id = user_id,
            role = role,
            rating = rating,
        )

        task.status = "completed"

        db.session.add(task)
        db.session.add(feedback)
        db.session.commit()

    if request.referrer and "requester" in request.referrer:
        returnObject = schema.create_requester_object(task)
    else: 
        returnObject = schema.create_fulfiller_object(task)    

    return render_template("accordion_entry.html", task=returnObject)

#Get all tasks that have a requestor_id of "requestor"
def tasks_for_requestor(requestor):
    data = flask.jsonify(\
        items=[item.serialize for item in\
               schema.Task.query.filter_by(requestor_id=requestor).all()]
    )
    return data

#Get all tasks that have a fulfiller_id of "fulfiller"
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(
                                      schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=[item.serialize for item in data])

#turn on text messages for a user for new tasks
def set_online():
    # Get current user
    user_id = int(current_user.get_id())
    flask_user = schema.Account.query.get(user_id)

    # Set user to be online
    flask_user.online = True;

    # add and commit changes
    db.session.commit()
    return ""

#turn off text messages for a user for new tasks
def set_offline():
    # Get current user
    user_id = int(current_user.get_id())
    flask_user = schema.Account.query.get(user_id)

    # Set user to be offline
    flask_user.online = False;

    # add and commit changes
    db.session.commit()
    return ""

#Get all entries with the current user as a requester for 
#the task history page for the current user.
def my_requester_tasks():
    user_id = flask.ext.login.current_user.get_id()
  
    #Separate requester tasks into three categories (open, in_progress, other) for easy display.
    tasks_open = schema.Task.query.filter_by(requestor_id=user_id).filter_by(
                                                            status="unassigned").all()
    tasks_in_progress = schema.Task.query.filter_by(requestor_id=user_id).filter_by(
                                                            status="in_progress").all()
    tasks_old = schema.Task.query.filter_by(requestor_id=user_id).filter(
                  schema.Task.status!="unassigned").filter(schema.Task.status!="in_progress").all()
    requester_objects_open = map(schema.create_requester_object, tasks_open)
    requester_objects_in_progress = map(schema.create_requester_object, tasks_in_progress)
    requester_objects_old = map(schema.create_requester_object, tasks_old)

    #Information for requester rating.
    num_tasks = len(schema.Feedback.query.filter_by(account_id = user_id).all())
    num_positive = len(schema.Feedback.query.filter_by(
                                account_id = user_id, rating = "positive").all())
    if num_tasks == 0:
        score = "none"
    else:
        score = str(int(num_positive * 100 / num_tasks)) + "%"

    return render_template("tasklist.html",
                            requestor_score= score,
                            tasks= (requester_objects_open +
                                    requester_objects_in_progress +
                                    requester_objects_old))

#Get task associated with an account_task entry
def get_task_from_account_task(account_task):
    task_id = account_task.task_id
    task = schema.Task.query.get(task_id)
    return task

#Get all entries with the current user as a fulfiller for 
#the task history page for the current user.
def  filler_tasks():
    user_id = flask.ext.login.current_user.get_id()

    conn = engine.connect()
    query = select([schema.account_task.c.task_id]).where(
                                      schema.account_task.c.account_id == user_id)
    account_tasks = conn.execute(query)

    tasks = map (get_task_from_account_task, account_tasks)

    #Separate tasks into two categories (in_progress and other) for easy display.
    tasks_in_progress = [elem for elem in tasks if elem.status == "in_progress"]
    tasks_old = [elem for elem in tasks if elem.status != "in_progress"]

    fulfiller_objects_in_progress = map(schema.create_fulfiller_object, tasks_in_progress)
    fulfiller_objects_old = map(schema.create_fulfiller_object, tasks_old)

    return render_template("tasklist.html",
                            tasks= (fulfiller_objects_in_progress +
                                    fulfiller_objects_old))

#Called to activate user after user clicks verification link in email.
def activate_user(verification_address):
    account = schema.Account.query.filter_by(email_hash=verification_address).first()
    if account is None:
        #if theres no account, then you can't activate
        return None
    else:
        #account has already been activated
        if account.activated:
            return False
        #activate the account
        else:
            account.activated = True
            db.session.add(account)
            db.session.commit()
            return True

#Verify email address that user is trying to register with is unique.
def is_email_used(email):
    result = schema.Account.query.filter_by(email=encryption.encrypt_string(email)).first() is not None
    return flask.jsonify(used=str(result))

#Verify phone number that user is trying to register with is unique.
def is_phone_used(phone):
    number_object = phonenumbers.parse(phone, "US")
    number_formatted = phonenumbers.format_number(number_object, phonenumbers.PhoneNumberFormat.NATIONAL)
    result = schema.Account.query.filter_by(phone=encryption.encrypt_string(number_formatted)).first() is not None
    return flask.jsonify(used=str(result))


def is_user_activated():
    return current_user.activated
