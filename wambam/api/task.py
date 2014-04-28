import flask
from flask import session, request, redirect, url_for, render_template
from flask.ext import sqlalchemy, restless, login as flask_login
from flask_login import current_user
from sqlalchemy import create_engine, select, event

import datetime
import time
import json
import phonenumbers

import schema
import emails
import encryption
import cool_word

db = None
engine = None

def setup_task_endpoints(app, database, eng):
    global db
    db = database

    global engine
    engine = eng

    #returns json with all of the tasks
    @app.route("/get_all_tasks")
    def get_all_tasks():
        return flask.jsonify(items=[i.serialize for i in schema.Task.query.all()])

    #returns json with all of the tasks that have not been assigned
    @app.route("/get_all_active_tasks")
    def get_all_active_tasks():
        return flask.jsonify(items=[i.serialize for i in 
                                    schema.Task.query.filter_by(status="unassigned").all()])

    #returns json with all of the tasks that have not been assigned
    @app.route("/get_all_claimed_tasks")
    def get_all_claimed_tasks():
        return flask.jsonify(items=[i.serialize for i in 
                                    schema.Task.query.filter_by(status="in_progress").all()])

    #Establish endpoints
    @app.route("/viewtaskjson/<int:taskid>") 
    def view_task_json(taskid):
        task = schema.Task.query.get(taskid)
        task_decrypted = encryption.decrypt_object(task)
        if (task is None):
            return flask.jsonify([])
        else:
            return flask.jsonify(task_decrypted)

    @app.route("/viewtaskdetails/<int:taskid>")
    def task_details_endpoint(taskid):
        return view_task_details(taskid)

    @app.route("/cancel_task/<int:task_id>", methods=["POST"])
    def cancel_endpoint(task_id):
        return cancel_task(task_id)

    @app.route("/finish_task/<int:task_id>", methods=["POST"])
    def finish_endpoint(task_id):
        return finish_task(task_id)

    @app.route("/submittask", methods=["POST"])
    def submit_endpoint():
        return submit()

    @app.route("/claimtask", methods=["POST"])
    def claim_endpoint():
        return claim()

#Returns decrypted task object in json.
def view_task_details(taskid):
    task = schema.Task.query.get(taskid)
    task_decrypted = encryption.decrypt_object(task)

    #If user tries to request task that does not exist, then they are rerouted to home page.
    if (task is None):
        return redirect("/home")
    else:
        #If the task is no longer available to be claimed, redirect user to concillatory page.
        if (task.status != "unassigned"):
          return redirect("/sorry")

        # Get email address of logged in user 
        email = encryption.decrypt_string(current_user.email)

        return render_template("taskview.html",
                                task_id = task.id,
                                lat = task_decrypted["latitude"],
                                lon = task_decrypted["longitude"],
                                title = task_decrypted["short_title"],
                                location = task_decrypted["delivery_location"],
                                bid = "$%(bid).2f" % {"bid": float(task_decrypted["bid"])},
                                expiration = schema.dump_datetime(task.expiration_datetime),
                                description = task_decrypted["long_title"],
                                email = email)



def cancel_task(task_id):
    task = schema.Task.query.get(task_id)

    #Someone other than task creator is trying to cancel the task!
    if task.requestor_id is not current_user.id:
        return redirect("/")

    #Only cancel the task if it is still in_progress
    if (task.status == "unassigned"):
        task.status = "canceled"

    db.session.add(task)
    db.session.commit()

    if request.referrer and "requester" in request.referrer:
        returnObject = schema.create_requester_object(task)
    else: 
        returnObject = schema.create_fulfiller_object(task)    

    #Return updated entry for task history page that will be loaded asyncronously on the page.
    return render_template("accordion_entry.html", task=returnObject)

#Mark task as complete
def finish_task(task_id):
    task = schema.Task.query.get(task_id)
    task.status = 'completed'
    db.session.add(task)
    db.session.commit()
    return ""

#Submit a new task
def submit():
    #Redirect user to home page if they did not specify a location that task is to occur at.
    if not ("lat" in session) or not ("lng" in session):
        return redirect(url_for("home"))

    title = request.form["title"]
    bid = request.form["bid"]
    bid = bid.replace("$","");
    expiration = request.form["expiration"]

    #format for timedelta is (days, seconds, microseconds, 
    #milliseconds, minutes, hours, weeks)
    expirationdate = datetime.datetime.now()
    if (expiration == "30min"):
        expirationdate += datetime.timedelta(0,0,0,0,30)
    elif (expiration == "1hr"):
        expirationdate += datetime.timedelta(0,0,0,0,0,1)
    elif (expiration == "1day"):
        expirationdate += datetime.timedelta(1)
    elif (expiration == "1wk"):
        expirationdate += datetime.timedelta(0,0,0,0,0,0,1)

    requestor_id = int(current_user.get_id())

    #Encrypt user data    
    encrypted = encryption.encrypt_dictionary(request.form)
    lat_encrypted = encryption.encrypt_string(session["lat"])
    lng_encrypted = encryption.encrypt_string(session["lng"])
    bid_encrypted = encryption.encrypt_string(bid)

    #Create task object
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
    first_name = encryption.decrypt_string(current_user.first_name)
    last_name = encryption.decrypt_string(current_user.last_name)

    # Get phone info for requester
    phone_number = encryption.decrypt_string(current_user.phone)
    phone_carrier = encryption.decrypt_string(current_user.phone_carrier)
    text_recipient = map(getTextRecipient, [phone_number], [phone_carrier])

    # Construct confirmation message for requester
    msg_subject = "Order Submitted"
    msg_body = "Your task request for '" + title + \
               "' has been placed! We'll text you when someone claims your task."

    # Send text message to requester asynchronously
    if request.referrer and request.referrer != '/test':
        emails.send_email(msg_subject, text_recipient, msg_body, msg_body)

    # Send alert text to all online fulfillers 
    fulfillers = schema.Account.query.filter(schema.Account.online == True).all()
    def getPhone(fulfiller):
        return encryption.decrypt_string(fulfiller.phone)
        
    def getPhoneCarrier(fulfiller):
        return encryption.decrypt_string(fulfiller.phone_carrier)

    fulfiller_phones = map(getPhone, fulfillers)
    fulfiller_carriers = map(getPhoneCarrier, fulfillers)

    text_fulfillers = map(getTextRecipient, fulfiller_phones, fulfiller_carriers)

    # Remove task requestor from list of potential fulfillers
    if text_recipient[0] in text_fulfillers:
        text_fulfillers.remove(text_recipient[0])
        
    if len(text_fulfillers) > 0:
        # Construct message for potential fulfillers
        msg_subject = "New Task Alert"
        msg_body = first_name + " " + last_name + " has created a task for '" + title + \
                  "'. Click the following link for more details: " + \
                  "http://wambam.herokuapp.com/viewtaskdetails/" + str(task.id) + " ."

        # Send text message to potential fulfillers
        if request.referrer and request.referrer != '/test':
            emails.send_email(msg_subject, text_fulfillers, msg_body, msg_body)

    return redirect("/confirm")


def claim():
    #Get task that was claimed
    task_num = int(request.form["id"])
    task = schema.Task.query.get(task_num)

    #Someone beat the potential fulfiller to the task!
    if (task.status != "unassigned"):
      return redirect("/sorry")

    decrypted_task = encryption.decrypt_object(task)
    title = decrypted_task["short_title"]
    location = decrypted_task["delivery_location"]
    bid = float(decrypted_task["bid"])
    expiration = schema.dump_datetime(task.expiration_datetime)
    description = decrypted_task["long_title"]

    # Get fulfiller
    fulfiller = current_user
    decrypted_fulfiller = encryption.decrypt_object(fulfiller)

    # Get requester
    current_task = schema.Task.query.get(task_num)
    requestor_id = current_task.requestor_id
    requestor = schema.Account.query.get(requestor_id)
    decrypted_requestor = encryption.decrypt_object(requestor)
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
    db.session.commit()

    # Get information on fulfiller to send confirmation text.
    fulfiller_number = decrypted_fulfiller["phone"]
    fulfiller_carrier = decrypted_fulfiller["phone_carrier"]
    text_fulfiller = getTextRecipient(fulfiller_number, fulfiller_carrier)

    # Construct message to send to fulfiller
    msg_subject = "Task Claimed"
    msg_body = "You have claimed the task '" + title + "'. Get in touch with " + \
               decrypted_requestor["first_name"] + " " + decrypted_requestor["last_name"] + \
               " at " + decrypted_requestor["phone"] + "."

    # Send message to fulfiller
    if request.referrer and request.referrer != '/test':
        emails.send_email(msg_subject, [text_fulfiller], msg_body, msg_body)

    # Get information on requester to send confirmation text.
    requestor_number = decrypted_requestor["phone"]
    requestor_carrier = decrypted_requestor["phone_carrier"]
    text_requestor = getTextRecipient(requestor_number, requestor_carrier)

    # Construct message to send to requestor
    msg_subject = "Your task has been claimed!"
    msg_body = decrypted_fulfiller["first_name"] + " " + decrypted_fulfiller["last_name"] + \
               " has claimed your task '" + title + "'. You can get in touch with " + \
               decrypted_fulfiller["first_name"] + " at " + decrypted_fulfiller["phone"] + "."

    # Send confirmation message to requestor
    if request.referrer and request.referrer != '/test':
        emails.send_email(msg_subject, [text_requestor], msg_body, msg_body)

    # Get confirmation word
    word = cool_word.get_cool_word()

    return render_template("confirmationwambam.html",
                            cool_word = word,
                            title = title,
                            location = location,
                            expiration = expiration,
                            description = description,
                            email = email,
                            bid = "$%(bid).2f" % {"bid": bid},
                            phone = decrypted_requestor["phone"],
                            desktop_client=request.cookies.get("mobile"))


#Helper method to get email address associated with user's phone number.
#We are using SMTP to SMS for our text messaging service because it's free :)
def getTextRecipient(phone_number, phone_carrier):
    #Cleanup the phone number
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
    else:                                  #The only other option is Verizon Wireless
        emailaddress += "@vtext.com"

    return emailaddress
