import random
import datetime
import time
import json
import os
import uuid
import requests

import flask
from flask import session, request, redirect, url_for, render_template
from flask.ext import sqlalchemy, restless, login as flask_login
from flask_login import current_user
from sqlalchemy import create_engine, select, event

import phonenumbers

import pytz
from pytz import timezone

import login
import schema
import emails
import encryption
import venmo
import task
import wambam_user

import datetime

from wambam import app

#global variable for the flask engine
engine = None

def register_events():
    ''' Event hooks for SQLAlchemy models. '''

    # When task data is pulled out: check for expiry
    @event.listens_for(schema.Task, 'load')
    def receive_load(target, context):
        for task in context.query.all():
            if datetime.datetime.now() > task.expiration_datetime and task.status == "unassigned":
                task.status = 'expired'

                db.session.add(task)
                db.session.commit()

def create_app():
    return flask.Flask(__name__)


def create_database(app):
    global engine

    # Create the Flask application and the Flask-SQLAlchemy object    
    app.config["DEBUG"] = True
    using_sqllite = False

    # get the database url from the environment variable
    try:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    except KeyError:
        # if it not found, create a new sqlite database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///tmp/' + uuid.uuid1().hex + '.db'
        using_sqllite = True

    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    
    # get the database object
    db = sqlalchemy.SQLAlchemy(app)
    schema.create_tables(app, db)

    #update the schema to the current version if necessary
    def initialize_database():
        print "Migrating database"

        #need to have a clean session before dropping tables
        db.session.commit()
        db.drop_all()
        db.create_all()

        # Add the version to the database
        version = schema.SchemaVersion(version=schema.current_schema_version)
        db.session.add(version)
        db.session.commit()

        print "Done Migrating"

    try:
        if using_sqllite or \
           schema.SchemaVersion.query.first().version is not schema.current_schema_version:
           
            initialize_database()
    except:
        #exception caused by version table not being in the database, which means we are working
        #with a clean postgres database
        initialize_database()

    # Register SQLAlchemy event hooks
    register_events()

    return db

def create_api(app, db):
    # Create the Flask-Restless API manager.
    manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

    # Create API endpoints, which will be available at /api/<tablename> by
    # default. Allowed HTTP methods can be specified as well.
    
    # allow clients to get entries and add entries
    manager.create_api(schema.Account, methods=["GET", "POST"])
    manager.create_api(schema.Task, methods=["GET", "POST"])
    manager.create_api(schema.Feedback, methods=["GET", "POST"])
    return manager


@app.before_request
def before_request():
    #exempt files are url's that do not require any authentication to access
    exempt_files = ["/check_email", "/check_phone", "/favicon.ico",
                    url_for("static", filename="login.css"), 
                    url_for("static", filename="login_mobile.css"),
                    url_for("static", filename="login_validator.js"),
                    "/get_user"]

    for f in exempt_files:
        if request.path == f:
            return None

    #trying to access an account activation page
    if request.path.startswith("/v/"):
        return None


    #trying to access an page only accessible if you are not logged in
    if request.path == "/" or request.path == "/mobile" or \
        request.path == "/login" or request.path == "/register":  

        #no need for them to access, go home
        if not current_user.is_anonymous() and login.is_session_valid():
            return redirect("/home")
    
    #trying to access a protected page
    else:
        #user is not valid
        if current_user.is_anonymous() or not login.is_session_valid():
            #we want to save the URL theyre trying to go to so we can
            #redirect them there after they log in
            if request.path.startswith("/viewtaskdetails/"):
                session["pre_login_url"] = request.path
            return redirect("/")

        #session is valid
        else:
            #update their token
            current_user.last_request = int(time.time())
            session["request_time"] = current_user.last_request
            db.session.commit()
            
            #if they"re not activated dont let them go anywhere
            if not current_user.activated and \
               not (request.path == "/home" or \
                request.path == "/logout" or \
                request.path.endswith(".css") or  \
                request.path.endswith(".js")):
                
                return redirect("/home")
                
app.config["SECRET_KEY"] = "I have a secret."
app.config["REMEMBER_COOKIE_DURATION"] = datetime.timedelta(days=14)

db = create_database(app)
api_manager = create_api(app,db)
login_manager = login.create_login_manager(app, db)

#encryption.setup_encyrption(app)
venmo.setup_venmo_endpoints(app, db, engine)
task.setup_task_endpoints(app, db, engine)
wambam_user.setup_user_endpoints(app, db, engine)
