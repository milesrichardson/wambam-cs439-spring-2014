import schema
import flask.ext.login

login_manager = None

def create_login_manager(app):
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

    @app.route('/login', methods=['POST'])
    def token_api():
        data = flask.request.get_json()
        email = data['email']
        password = data['password']

        user = schema.Account.query.filter_by(email=email).filter_by(password_hash=password).first()

        if user is None:
            flask.abort(401)
        else:
            flask.ext.login.login_user(user, remember=True)
            return flask.redirect("/")

    return login_manager
