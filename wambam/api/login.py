from user import User
import schema

login_manager = None

def authenticate(username, password):
    user = schema.Account.query.filter_by(username=username, password=password).first()
    return (user is not None)


def create_login_manager(app):
    global login_manager
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(userid):
        account = schema.Account.query.get(int(userid))
        return User(u.last_name, u.id)
    
    @app.route('/login', methods=['POST'])
    def login():
        username = request.form['username']
        password = request.form['password']
        if authenticate(username, password):
            return "yay"

        return "shit"


    return login_manager


