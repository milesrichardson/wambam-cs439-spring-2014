import flask.ext.login

class User(login.UserMixin):
    def __init__(self, name,userid, authenticated=False, active=False):
        super(User, self).__init__()
        self.name = name
        self.id = int(userid)
        self.authenticated = authenticated
        self.active = active

