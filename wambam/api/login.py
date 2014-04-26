import flask.ext.login
from flask.ext.login import current_user
from flask import render_template, session

import sqlalchemy

import encryption
import phonenumbers
import time

import schema

login_manager = None
db = None

def create_login_manager(app, db):
    global login_manager
    login_manager = flask.ext.login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(userid):
        return schema.Account.query.get(int(userid))

    @login_manager.token_loader
    def load_token(token):
        try:
            user = schema.Account.verify_auth_token(token)
            return user
        except:
            return None

    @app.route("/login", methods=["POST"])
    def user_login():
        if flask.request.method == "POST":

            #User is attempting to log in
            if "userfield" in flask.request.form:
                username = flask.request.form["userfield"]
                password = flask.request.form["passwordfield"]

            #User is trying to register
            else:
                username = flask.request.form["email"]
                password = flask.request.form["password"]
            
            #Since we allow the user to log in with either an email address or a phone number,
            #we must handle both cases. 
            if "@"  not in username:
                try:
                    #Assume it is a phone number and try to parse.
                    number_object = phonenumbers.parse(username, "US")
                    username = phonenumbers.format_number(number_object,
                                                          phonenumbers.PhoneNumberFormat.NATIONAL)
                except:
                    #Parse failed. Not a valid phone number or email address.
                    return render_template("login.html", error_msg="Invalid email or phone number")

            username = encryption.encrypt_string(username)
            password = encryption.encrypt_string(password)

            #Log in with user's encrypted username and password, trying username as both a phone
            #number and as an email address.
            user = schema.Account.query.filter(sqlalchemy.or_(schema.Account.email==username,
                        schema.Account.phone==username)).filter_by(password=password).first()
                    
            #Log in credential were invalid
            if user is None:
                app.logger.debug("Bad login")
                return render_template("login.html", error_msg="Invalid login")
            else:
                #Save the logged in user and the time.
                flask.ext.login.login_user(user, remember=True)
                user.last_request = int(time.time())
                flask.session["request_time"] = user.last_request
                db.session.commit()

                #Redirect the user to a mobile task details page if they originally requested it
                #Otherwise, request them to the home page.
                try:
                    next = flask.request.form["next"]
                except:
                    next = "/home"

                return flask.redirect(next)
        else:
            return flask.abort(401)

    #Logout user and reroute user to login page.
    @app.route("/logout")
    def user_logout():
        user = flask.ext.login.current_user
        if not user.is_anonymous():
            user.last_request = 0
            db.session.commit()
        flask.session.clear() 
        flask.ext.login.logout_user()
        return flask.redirect("/")

    login_manager.login_view = "/login"
    return login_manager


#Session is invalid if last log in was sufficiently long ago.
def is_session_valid():
    if current_user.last_request == 0 or \
      "request_time" not in session or \
       session["request_time"] + 36000000 < current_user.last_request:
       
        return False
    return True
