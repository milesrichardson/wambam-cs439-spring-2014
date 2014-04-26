import flask
from flask import Flask
from flask import request, redirect, url_for, session, render_template
from flask_mail import Message, Mail
from sqlalchemy import create_engine, select

import json
import requests
import hashlib

from wambam import app
import api
import cool_word
import schema
import emails
import wambam_user

flask_pos = []

#Route user to the login page if they are not logged in.
@app.route("/")
def hello():
    try:
        pre_login_url = session["pre_login_url"]
    except:
        pre_login_url = "/"

    return render_template("login.html", pre_login_url=pre_login_url)

#Route user to the mobile login page if they are not logged in and on a mobile device
@app.route("/mobile")
def hello_mobile():
    try:
        pre_login_url = session["pre_login_url"]
    except:
        pre_login_url = "/"

    return render_template("login_mobile.html", pre_login_url=pre_login_url)

#Page for creating tasks
@app.route("/home")
def home():
    return render_template("index1.html", activated=wambam_user.is_user_activated())

#Page for fulfilling tasks
@app.route("/working")
def working():
    return render_template("working.html")

#Actually perform login
@app.route("/login", methods=["POST"])
def login():
    user = request.form["userfield"]
    password = request.form["passwordfield"]
    return redirect(url_for("home"))

#Determine if email address is unique
@app.route("/check_email", methods=["POST"])
def check_email():
    email = request.get_json()["email"]
    return wambam_user.is_email_used(email)

#Determine if phone number is unique
@app.route("/check_phone", methods=["POST"])
def check_phone():
    phone = request.get_json()["phone"]
    return wambam_user.is_phone_used(phone)

#Create a new user
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

    #Text version of email to send to activate account
    body = "Welcome to WamBam!<br><br>You're almost good to go." + \
           " Just follow this link to activate your account: http://wambam.herokuapp.com/v/"+ \
            verification_address + "<br><br>Yours truly,<br>The WamBam! Team"

    #HTML version
    html = "<div style='background: #0F4D92; color: white; font-size:20px; padding-top: 10px;" + \
           " padding-bottom: 10px; padding-left: 20px'> WamBam! </div><br>" + \
           " <div style='padding-left: 20px'>" + \
           body + \
           "</div>"

    emails.send_email(subject, recipients, body, html)

    wambam_user.add_user(user)
    return redirect("/login", code=307)

#First stage in creating a task.      
@app.route("/addtask", methods=["POST"])
def index():
    session["lat"] = request.form["lat"]
    session["lng"] = request.form["lng"]
    return redirect(url_for("construct"))

#Finished second stage of creating a task
@app.route("/constructtask")
def construct():
    return render_template("addtask.html", desktop_client=request.cookies.get("mobile"))

@app.route("/dotask")
def execute():
    return render_template("taskserver.html")

#Confirmation page
@app.route("/confirm")
def confirm():
    word = cool_word.get_cool_word()
    return render_template("confirmation.html",
                            cool_word = word)
@app.route("/tasklist")
def tasklist():
    return render_template('tasklist.html')

#Page to tell user task has already been claimed.
@app.route("/sorry")
def sorry():
    return render_template("alreadyclaimed.html")

#Endpoint to activate an acocunt
@app.route("/v/<verification_address>", methods=["GET"])
def verify(verification_address):
    result = wambam_user.activate_user(verification_address)
    if result is None:
        return redirect("/home")
    if result:
        message = "Congratulations your account is activated!"
    else:
        message = "Your account was already activated."

    return render_template("activation.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)
