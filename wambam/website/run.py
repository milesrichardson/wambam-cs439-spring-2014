from flask import Flask
from flask import request, redirect, url_for, session
from flask import render_template
from flask_mail import Message
from flask_mail import Mail
import json
import requests

from wambam import app

app.secret_key="wambam"

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'wambamapp@gmail.com',
    MAIL_PASSWORD = 'wambam123',
    MAIL_DEFAULT_SENDER = 'wambamapp@gmail.com'
))

mail = Mail(app)

flask_pos = []

@app.route("/")
def hello():
    return render_template('login.html')

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

@app.route("/register", methods=['POST'])
def register():
    phone = request.form['phone']
    email = request.form['email']
    password = request.form['password']
    passwordconfirm = request.form['passwordconfirm']

    #Email client to complete registration
    msg = Message(subject="Complete Your WamBam! Registration",
                  recipients=[email],
                  body="Welcome to WamBam!\r\n\r\nYou're almost good to go. Just follow this link to activate your account: http://127.0.0.1:5000/home\r\n\r\nYours truly,\r\nThe WamBam! Team",
                  html="<div style='background: #0F4D92; color: white; font-size:20px; padding-top: 10px; padding-bottom: 10px; padding-left: 20px'> WamBam! </div><br> <div style='padding-left: 20px'>Welcome to WamBam!<br><br>You're almost good to go. Just follow this link to activate your account: http://127.0.0.1:5000/home<br><br>Yours truly,<br>The WamBam! Team</div>")
    mail.send(msg)

    return redirect(url_for('home'))
      
@app.route("/addtask", methods=['POST'])
def index():
    session['lat'] = request.form['lat']
    session['lng'] = request.form['lng']
    return redirect(url_for('construct'))

@app.route("/constructtask")
def construct():
    return render_template('addtask.html')

@app.route("/submittask", methods=['POST'])
def submit():
    app.logger.debug("/submittask")
    app.logger.debug("2 submittask")
    if not ('lat' in session) or not ('lng' in session):
        return redirect(url_for('working'))
    app.logger.debug("3 submittask")
    lat = session['lat']
    app.logger.debug("4 submittask")
    lng = session['lng']
    app.logger.debug("5 submittask")
    title = request.form['title']
    app.logger.debug("6 submittask")
    location = request.form['location']
    app.logger.debug("7 submittask")
    bid = request.form['bid']
    app.logger.debug("8 submittask")
    expiration = request.form['expiration']
    app.logger.debug("9 submittask")
    description = request.form['description']
    app.logger.debug("10 submittask")

    app.logger.debug("middle submittask")

    task = {
        'requestor_id': '42',
        'coordinates': lat + ',' + 'long',
        'short_title': title,
        'long_title': description,
        'bid': bid,
        'expiration_datetime': None,
        'status': 'unassigned'
    }

    r = requests.post('~/api/task', data=json.dumps(task),
                       headers={'content-type': 'application/json'})
    app.logger.debug(r)

    session.clear()

    app.logger.debug("end submittask")
    return redirect(url_for('confirm'))

@app.route("/dotask")
def execute():
    return render_template('taskserver.html')

@app.route("/confirmWamBam", methods=['GET', 'POST'])
def wambam():

    title = request.form['title']
    location = request.form['location']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']
    email = request.form['email']

    return render_template('confirmationwambam.html',
                            title=title,
                            location=location,
                            bid=bid,
                            expiration=expiration,
                            description=description,
                            email=email,
                            phone="770-362-9815")

@app.route("/confirm")
def confirm():
    return render_template('confirmation.html')

if __name__ == "__main__":
    app.run(debug=True)
