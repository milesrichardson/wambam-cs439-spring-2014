from flask import Flask
from flask import request, redirect, url_for
from flask import render_template
from flask_mail import Message
from flask_mail import Mail

app = Flask(__name__)

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
      
@app.route("/addtask")
def index():
    return render_template('addtask.html')

@app.route("/submittask", methods=['POST'])
def submit():
    title = request.form['title']
    location = request.form['deliveryloc']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']
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
