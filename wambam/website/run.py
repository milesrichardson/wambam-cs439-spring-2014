import flask
from flask import Flask
from flask import request, redirect, url_for, session, render_template
from flask_mail import Message, Mail

import json
import requests
import hashlib

from wambam import app
import api
import schema
import emails

flask_pos = []

@app.route("/")
def hello():
    try:
        pre_login_url = session["pre_login_url"]
    except:
        pre_login_url = "/"


    return render_template("login.html", pre_login_url=pre_login_url)

@app.route("/mobile")
def hello_mobile():
    try:
        pre_login_url = session["pre_login_url"]
    except:
        pre_login_url = "/"

    return render_template("login_mobile.html", pre_login_url=pre_login_url)

@app.route("/home")
def home():
    return render_template("index1.html", activated=api.is_user_activated())

@app.route("/working")
def working():
    return render_template("working.html")

@app.route("/login", methods=["POST"])
def login():
    user = request.form["userfield"]
    password = request.form["passwordfield"]
    return redirect(url_for("home"))

@app.route("/check_email", methods=["POST"])
def check_email():
    email = request.get_json()["email"]
    return api.is_email_used(email)

@app.route("/check_phone", methods=["POST"])
def check_phone():
    phone = request.get_json()["phone"]
    return api.is_phone_used(phone)

@app.route("/register", methods=["POST"])
def register():

    user = {}
    user["phone"] = request.form["phone"]
    user["phone_carrier"] = request.form["phonecarrier"]
    user["email"] = request.form["email"]
    user["pwd"] = request.form["password"]
    user["first_name"] = request.form["firstname"]
    user["last_name"] = request.form["lastname"]
    passwordconfirm = request.form["passwordconfirm"]

    verification_address = hashlib.sha224(user["email"] + app.config["SECRET_KEY"]).hexdigest()
    user["verification_address"] = verification_address


    # Email client to complete registration
    subject = "Complete Your WamBam! Registration"
    recipients = [user["email"]]

    body = "Welcome to WamBam!<br><br>You're almost good to go. Just follow this link to activate your account: http://wambam.herokuapp.com/v/"+ verification_address + "<br><br>Yours truly,<br>The WamBam! Team"

    html = "<div style='background: #0F4D92; color: white; font-size:20px; padding-top: 10px; padding-bottom: 10px; padding-left: 20px'> WamBam! </div><br> <div style='padding-left: 20px'>" +\
           body + \
           "</div>"

    emails.send_email(subject, recipients, body, html)

    app.logger.debug("Before adding user after registration")    
    api.add_user(user)
    return redirect("/login", code=307)
      
@app.route("/addtask", methods=["POST"])
def index():
    session["lat"] = request.form["lat"]
    session["lng"] = request.form["lng"]
    return redirect(url_for("construct"))

@app.route("/constructtask")
def construct():
    return render_template("addtask.html", desktop_client=request.cookies.get("mobile"))

@app.route("/dotask")
def execute():
    return render_template("taskserver.html")

@app.route("/confirm")
def confirm():
    cool_word = api.get_cool_word()
    return render_template("confirmation.html",
                            cool_word = cool_word)

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
        'fulfiller_email': fulfiller_email,
        'fulfiller_phone': fulfiller_phone,
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
    tasks = schema.Task.query.filter_by(requestor_id=user_id).all()
    requester_objects = map(create_requester_object, tasks)
    return render_template("tasklist.html",
                            tasks= requester_objects)

@app.route("/my_fulfiller_tasks")
def my_fulfiller_tasks():
    user_id = flask.ext.login.current_user.get_id()
    tasks = schema.Task.query.filter_by(fulfiller_id=user_id).all()
    return render_template("tasklist.html",
                            tasks= tasks)

@app.route("/sorry")
def sorry():
    return render_template("alreadyclaimed.html")

@app.route("/v/<verification_address>", methods=["GET"])
def verify(verification_address):
    result = api.activate_user(verification_address)
    if result is None:
        return redirect("/home")
    if result:
        message = "Congratulations your account is activated!"
    else:
        message = "Your account was already activated."

    return render_template("activation.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)
