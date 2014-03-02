import schema
import flask.ext.login
import sqlalchemy
import time

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

    @app.route('/login', methods=['POST', 'GET'])
    def user_login():
        if flask.request.method == 'POST':
            data = flask.request.get_json()
            remember = False
            if data is not None:
                username = data['userfield']
                password = data['passwordfield']
                remember = True
            else:
                username = flask.request.form['userfield']
                password = flask.request.form['passwordfield']
                if 'rememberfield' in flask.request.form:
                    remember = True
                    
            user = schema.Account.query.filter(sqlalchemy.or_(schema.Account.email==username, schema.Account.phone==username)).filter_by(password_hash=password).first()
                    
            if user is None:
                flask.abort(401)
            else:
                flask.ext.login.login_user(user, remember=True)
                user.last_request = int(time.time())
                flask.session['request_time'] = user.last_request
                db.session.commit()
                return flask.redirect(flask.request.args.get('next') or "/")
        else:
            return flask.abort(401)

    @app.route('/logout')
    def user_logout():
        user = flask.ext.login.current_user
        if not user.is_anonymous():
            user.last_request = 0
            db.session.commit()
        flask.ext.login.logout_user()
        return flask.redirect("/")

#    app.config['REMEMBER_COOKIE_DOMAIN']='.'+app.config['SERVER_NAME']
    login_manager.login_view = '/login'
    return login_manager

