from flask import Flask
from flask import request, redirect, url_for, session
from flask import render_template
from flask_mail import Message
from flask_mail import Mail
import json
import requests

from wambam import app
import api
import emails

app.secret_key="wambam"


flask_pos = []

@app.route("/")
def hello():
    try:
        pre_login_url = session['pre_login_url']
    except:
        pre_login_url = '/'

    return render_template('login.html', pre_login_url=pre_login_url)

@app.route("/mobile")
def hello_mobile():
    try:
        pre_login_url = session['pre_login_url']
    except:
        pre_login_url = '/'

    return render_template('login_mobile.html', pre_login_url=pre_login_url)

@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/working")
def working():
    return render_template('working.html')

@app.route("/login", methods=['POST'])
def login():
    user = request.form['userfield']
    password = request.form['passwordfield']
    return redirect(url_for('home'))

@app.route("/check_email", methods=['POST'])
def check_email():
    email = request.get_json()['email']
    return api.is_email_used(email)

@app.route("/check_phone", methods=['POST'])
def check_phone():
    phone = request.get_json()['phone']
    return api.is_phone_used(phone)

@app.route("/register", methods=['POST'])
def register():

    user = {}
    app.logger.debug("Before adding phone after registration")    
    user["phone"] = request.form['phone']
    app.logger.debug("Before adding pc after registration")    
    user["phone_carrier"] = request.form['phonecarrier']
    app.logger.debug("Before adding email after registration")    
    user["email"] = request.form['email']
    user["pwd"] = request.form['password']
    user["first_name"] = request.form['firstname']
    user["last_name"] = request.form['lastname']
    passwordconfirm = request.form['passwordconfirm']

    # Email client to complete registration
    subject = "Complete Your WamBam! Registration"
    recipients = [user["email"]]
    body = "Welcome to WamBam!\r\n\r\nYou're almost good to go. Just follow this link to activate your account: http://wambam.herokuapp.com/home\r\n\r\nYours truly,\r\nThe WamBam! Team"
    html = "<div style='background: #0F4D92; color: white; font-size:20px; padding-top: 10px; padding-bottom: 10px; padding-left: 20px'> WamBam! </div><br> <div style='padding-left: 20px'>Welcome to WamBam!<br><br>You're almost good to go. Just follow this link to activate your account: http://wambam.herokuapp.com/home<br><br>Yours truly,<br>The WamBam! Team</div>"
    emails.send_email(subject, recipients, body, html)

    app.logger.debug("Before adding user after registration")    
    api.add_user(user)
    return redirect('/login', code=307)
      
@app.route("/addtask", methods=['POST'])
def index():
    session['lat'] = request.form['lat']
    session['lng'] = request.form['lng']
    return redirect(url_for('construct'))

@app.route("/constructtask")
def construct():
    return render_template('addtask.html', desktop_client=request.cookies.get('mobile'))

@app.route("/dotask")
def execute():
    return render_template('taskserver.html')

@app.route("/confirm")
def confirm():
    return render_template('confirmation.html')

if __name__ == "__main__":
    app.run(debug=True)
