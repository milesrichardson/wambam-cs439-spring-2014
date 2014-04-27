import json
import requests

import flask
from flask import session, request, redirect
from flask.ext import sqlalchemy, login as flask_login
from flask_login import current_user
from sqlalchemy import create_engine, select, event

import schema
import encryption


db = None
engine = None

def redirect_to_venmo():
    return redirect("https://api.venmo.com/v1/oauth/authorize" + \
                    "?client_id=1687&scope=make_payments%20access_profile&response_type=token")

def setup_venmo_endpoints(app, database, eng):
    global db
    db = database
    
    global engine
    engine = eng

    @app.route("/venmo_auth")
    def venmo_auth():
        return get_venmo_token()

    @app.route("/setup_venmo_id")
    def venmo_id():
        return setup_venmo_id()

    @app.route("/venmo_make_payment", methods=["POST"])
    def make_payment():
        return make_venmo_payment()

#Get user's venmo access token after they complete transaction on Venmo.
def get_venmo_token():
    token = request.args.get("access_token", None)
    if "post_venmo_url" not in session:
        print "Non-existent venmo URL in Session!"
        return redirect("/my_requester_tasks")

    redirect_to = session["post_venmo_url"]
    del session["post_venmo_url"]

    if token is not None:
        current_user.venmo_token = encryption.encrypt_string(token)
        db.session.add(current_user)
        db.session.commit()
        return redirect(redirect_to)
    else:
        return redirect("/my_requester_tasks")

def setup_venmo_id():
    #get venmo token
    if current_user.venmo_token == "":
        session["post_venmo_url"] = request.path
        return redirect_to_venmo()

    #redirect authenticate to venmo
    else:
        url = "https://api.venmo.com/v1/me?access_token=" + \
              encryption.decrypt_string(current_user.venmo_token)
        response = requests.get(url)
        current_user.venmo_token = "";
        response_dict = json.loads(response.text)

        #Get venmo information for user if error did not occur.
        if "error" not in response_dict:
            venmo_id = response_dict["data"]["user"]["id"]
            current_user.venmo_id = encryption.encrypt_string(venmo_id)
            db.session.add(current_user)
            db.session.commit()
        return redirect("/my_requester_tasks")

#Allow a requester to pay a fulfiller through Venmo. 
def make_venmo_payment():
    task_id = request.form["task_id"]
    if task_id is None:
        return ""

    task = schema.Task.query.get(task_id)

    #Send the user to venmo if they have not been authenticated yet.
    if current_user.venmo_token == "":
        session["post_venmo_url"] = request.path
        return redirect_to_venmo()

    #The user must have already been authenticated on Venmo.
    else:
        if task.requestor_id is not current_user.id:
            return ""

        #Carry out the payment.
        conn = engine.connect()
        query = select([schema.account_task.c.account_id]).where(
                            schema.account_task.c.task_id == task_id)
        account_tasks = conn.execute(query)
        accounts = map (get_account_from_account_task, account_tasks)
        fulfiller_account = accounts[0]

        data = {
            "access_token":encryption.decrypt_string(current_user.venmo_token),
            "user_id":encryption.decrypt_string(schema.Account.get(fulfiller_account.id).venmo_id),
            "note":"A Wambam! payment for: " + encryption.decrypt_string(task.title),
            "amount":encryption.decrypt_string(task.bid)
        }

        #Send payment to Venmo
        response = requests.post("https://api.venmo.com/v1/payments", data)
        response_dict = json.loads(response.text)

        #Payment was unsuccessful for some reason.
        if response_dict["data"]["payment"]["status"] == "failed":
            pass

        db.session.add(current_user)
        db.session.commit()
        return ""

#Test if user has registered their Venmo account with WamBam!
def can_use_venmo(task_id):
    if task_id is None:
        return "false"
    task = schema.Task.query.get(task_id)
    conn = engine.connect()
    query = select([schema.account_task.c.account_id]).where(
                               schema.account_task.c.task_id == task_id)
    account_tasks = conn.execute(query)
    accounts = map (get_account_from_account_task, account_tasks)
    fulfiller_account = accounts[0]

    if schema.Account.query.get(fulfiller_account.id).venmo_id == "":
        return "false"
    return "true"

#Get account associated with an account_task entry.
def get_account_from_account_task(account_task):
    account_id = account_task.account_id
    account = schema.Account.query.get(account_id)
    return account
