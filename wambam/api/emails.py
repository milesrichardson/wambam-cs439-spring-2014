from flask_mail import Message
from flask_mail import Mail
from threading import Thread
from wambam import app

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

def send_async_email(msg):
    with app.app_context():
      mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients = recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target = send_async_email, args = [msg])
    thr.start()
