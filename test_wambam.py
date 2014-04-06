import os
import uuid
from wambam import app
import unittest
import tempfile
import json

class TestWambam(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            userfield=username,
            passfield=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('admin', 'default')
        rv = self.logout()


if __name__ == "__main__":
    unittest.main()
