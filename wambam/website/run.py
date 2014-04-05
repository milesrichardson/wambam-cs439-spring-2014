from flask import Flask
from flask import request, redirect, url_for, session, render_template
from flask_mail import Message, Mail

import json
import requests
import hashlib

from wambam import app
import api
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
