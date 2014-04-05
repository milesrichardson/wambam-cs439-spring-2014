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

    @app.route("/login", methods=["POST"])
    def user_login():
        if flask.request.method == "POST":
            #used the login page
            if "userfield" in flask.request.form:
                username = flask.request.form["userfield"]
                password = flask.request.form["passwordfield"]
            #went through the register
            else:
                username = flask.request.form["email"]
                password = flask.request.form["password"]
                    
            user = schema.Account.query.filter(sqlalchemy.or_(schema.Account.email==username, schema.Account.phone==username)).filter_by(password_hash=password).first()
                    
            if user is None:
                app.logger.debug("abort")
                flask.abort(401)
            else:
                flask.ext.login.login_user(user, remember=True)
                user.last_request = int(time.time())
                flask.session["request_time"] = user.last_request
                db.session.commit()

                try:
                    next = flask.request.form["next"]
                except:
                    next = "/home"

                return flask.redirect(next)
        else:
            return flask.abort(401)

    @app.route("/logout")
    def user_logout():
        user = flask.ext.login.current_user
        if not user.is_anonymous():
            user.last_request = 0
            db.session.commit()
        flask.session.clear() #VERY DANGEROUS, USE AT OWN RISK!
        flask.ext.login.logout_user()
        return flask.redirect("/")

    login_manager.login_view = "/login"
    return login_manager
