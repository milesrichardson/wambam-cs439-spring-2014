from flask_mail import Message, Mail
from threading import Thread
from wambam import app

#update app with configuration settings for sending emails
app.config.update(dict(
    DEBUG = False,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = "wambamapp@gmail.com",
    MAIL_PASSWORD = "wambam123",
    MAIL_DEFAULT_SENDER = "wambamapp@gmail.com"
))

#Create mail object
mail = Mail(app)

#Helper function to allow emails/texts to be sent asynchronously.
def send_async_email(msg):
    with app.app_context():
      mail.send(msg)

#Sends email/text in separate thread.
def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients = recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target = send_async_email, args = [msg])
    thr.start()
