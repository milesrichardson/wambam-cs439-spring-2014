import os
import uuid
import unittest
import datetime
import tempfile
import json
import sys

sys.path.append("wambam/api")

import api
import schema

class TestWambam(unittest.TestCase):

    def setUp(self):
        self.app = api.create_app()
        self.app.config["SECRET_KEY"] = "I have a secret....."
        self.app.config["REMEMBER_COOKIE_DURATION"] = datetime.timedelta(days=14)
        self.db = api.create_database(self.app)
        api_manager = api.create_api(self.app,self.db)

        #self.addBaseUsers()
        #self.addBaseTasks()


    def login(self, username, password):
        return self.app.post('/login', data=dict(
            userfield=username,
            passfield=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def testInsertTask(self):
        result = [i.serialize for i in schema.Task.query.all()]
        self.assertEqual(len(result) , 4)

    def testInsertUser(self):
        result = [i.serialize for i in schema.Account.query.all()]
        self.assertEqual(len(result) , 1)

    def addBaseTasks(self):
        task1 = schema.Task(
            requestor_id=1,
            latitude = 41.3111,
            longitude = -72.9267,
            short_title="Title 1",
            bid=float(1),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 1",
            delivery_location="CEID",
            status="in_progress")

        task2 = schema.Task(
            requestor_id=1,
            latitude = 41.3121,
            longitude = -72.9277,
            short_title="Title 2",
            bid=float(5),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 2",
            delivery_location="Saybrook",
            status="unassigned")

        task3 = schema.Task(
            requestor_id=1,
            latitude = 41.3101,
            longitude = -72.9257,
            short_title="Title 3",
            bid=float(10),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 3",
            delivery_location="There",
            status="completed")

        task4 = schema.Task(
            requestor_id=1,
            latitude = 41.3131,
            longitude = -72.9287,
            short_title="Title 4",
            bid=float(15),
            expiration_datetime=datetime.datetime.now(),
            long_title="This is description 4",
            delivery_location="Here",
            status="expired")

        self.db.session.add(task1) 
        self.db.session.add(task2)
        self.db.session.add(task3) 
        self.db.session.add(task4) 
        self.db.session.commit()


    def addBaseUsers(self):

        user = schema.Account(
            activated=True,
            phone="7703629815",
            phone_carrier="AT&T",
            email="michael.hopkins@yale.edu",
            password_hash="blah",
            online=True,
            first_name="Michael",
            last_name="Hopkins")

        self.db.session.add(user)
        self.db.session.commit()


if __name__ == "__main__":
    unittest.main()
