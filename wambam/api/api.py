import flask
import flask.ext.sqlalchemy
import flask.ext.restless
import uuid
import flask.ext.login
from flask import session, request, redirect, url_for

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import schema
from wambam import app

def create_app():
    return flask.Flask(__name__)

def create_database(app):
    # Create the Flask application and the Flask-SQLAlchemy object
    
    # generate a new name for the database each time, for testing purposes
    db_name = uuid.uuid1().hex

    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/' + db_name + '.db'
    
    # get the database object
    db = flask.ext.sqlalchemy.SQLAlchemy(app)
    schema.create_tables(db)

    # Create the database tables.
    db.create_all()

    michael = schema.Account(
    phone="7703629815",
    email="michael.hopkins@yale.edu",
    online=True,
    first_name="Michael",
    last_name="Hopkins")

    db.session.add(michael)
    db.session.commit()

    return db


def create_api(app, db):
    # Create the Flask-Restless API manager.
    manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

    # Create API endpoints, which will be available at /api/<tablename> by
    # default. Allowed HTTP methods can be specified as well.
    
    manager.create_api(schema.Account, methods=['GET', 'POST', 'DELETE', 'PATCH'])
    manager.create_api(schema.Task, methods=['GET', 'POST', 'DELETE'])
    return manager

db = create_database(app)
api_manager = create_api(app,db)
login_manager = flask.ext.login.LoginManager()
login_manager.init_app(app)

def _token_loader(token):
    try:
        user = schema.Account.verify_auth_token(token)
        return user
    except:
        pass


login_manager.token_loader(_token_loader)

@app.route('/get_all_active_tasks')
def get_all_active_tasks():
    return flask.jsonify(items=[i.serialize for i in schema.Task.query.filter_by(status='unassigned').all()])

@app.route('/tasks_for_requestor/<int:requestor>')
def tasks_for_requestor(requestor):
    return flask.jsonify(items=schema.Task.query.filter_by(requestor_id=requestor).all())

@app.route('/tasks_for_fulfiller/<int:fulfiller>')
def tasks_for_fulfiller(fulfiller):
    data = schema.Task.query.filter(schema.Task.fulfiller_accounts.any(schema.Account.id == fulfiller)).all()
    return flask.jsonify(items=data)

@app.route('/api/token', methods=['POST'])
def token_api():

    email = flask.request.values.get('email')
    password = flask.request.values.get('password')

    return email + ' ' + password
    user = schema.Account.query.filter_by(email=email).filter_by(password_hash=password).first()
    if user is None:
        flask.abort(401)
    else:
        token = user.generate_auth_token()
        
    return token

@app.route("/submittask", methods=['POST'])
def submit():
    if not ('lat' in session) or not ('lng' in session):
        return redirect(url_for('working'))

    lat = session['lat']
    lng = session['lng']
    title = request.form['title']
    location = request.form['location']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']

    task = schema.Task(
        requestor_id='1',
        coordinates= lat + ',' + lng,
        short_title=title,
        long_title=description,
        bid=float(bid),
        expiration_datetime=None,
        status='unassigned')

    db.session.add(task)
    db.session.commit()
    session.clear()

    app.logger.debug("end submittask")
    return redirect(url_for('confirm'))

app.jinja_env.globals.update(get_all_active_tasks=get_all_active_tasks)

