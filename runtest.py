import ast
import datetime
import os
import re
import unittest
import sys

postgres = None
if "DATABASE_URL" in os.environ:
    postgres = os.environ["DATABASE_URL"]
    del os.environ["DATABASE_URL"]

from wambam import app

if postgres is not None:
    os.environ["DATABASE_URL"] = postgres

import schema
port = int(os.environ.get('PORT', 5000))

sys.path.insert(0, "./wambam/api/")
import encryption

class TestWambam(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app_client = app.test_client()
        self.app.config["SECRET_KEY"] = "I have a secret."
        
        #There are 4 tasks in the DB initially. 
        #Two are unclaimed. AddClaimTask is the first test which will
        #claim a task. AddSubmittedTask will create a new task, so
        #the num_tasks variable reflects these stats for the other tests
        self.num_tasks = {'all':5, 
                          'active':2,
                          'claimed':0,
                          'as_requestor':5,
                          'as_fulfiller':1}
        self.username = "michael.hopkins@yale.edu"
        self.password = "blah"

    def login(self):
        return self.app_client.post('/login', data=dict(
            userfield=self.username,
            passwordfield=self.password
        ), follow_redirects=True)

    #Forced to happen first
    def testAddClaimTask(self):
        self.login()
        result = self.app_client.post('/claimtask', data=dict(
            id=1), headers={'Referer': '/test'},
            follow_redirects=True)

    #This tests AddClaimTask as well
    def testAddFeedback(self):
        self.login()
        result = self.app_client.post('/add_feedback/1/positive', headers={'Referer': '/test'})

        time_regex = re.compile(".*[0-9]+:[0-9]+ (AM|PM) EDT</label>")

        expected = open('./test_htmls/feedback.html', 'r')
        for line in result.data.split('\n'):
            test_line = expected.readline().strip()
            if time_regex.match(test_line):
                continue
            self.assertEqual(test_line, line.strip())

        expected.close()

    #Forced to happen first
    def testAddSubmitTask(self):
        self.login()
        with self.app_client.session_transaction() as sess:
            sess['lat'] = "41.3084304"
            sess['lng'] = "-72.9284356"
        result = self.app_client.post('/submittask', data=dict(
            title='test_submit_task',
            bid='$3', 
            expiration='30min',
            description='N/A',
            location='Branford'), headers={'Referer': '/test'}, 
                follow_redirects=True) 

        #Verify that it's listed as an active task
        result = self.app_client.get('/get_all_active_tasks', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks) , self.num_tasks['active'])


    def testGetUser(self):
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertEqual(user, {})

        self.login()
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertEqual(user['email'], self.username)


    def testLoginLogout(self):
        self.login()

        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertEqual(user['email'], self.username)

        self.app_client.get('/logout', follow_redirects=True)
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertEqual(user, {})

    def testAllTasks(self):
        self.login()
        result = self.app_client.get('/get_all_tasks', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks) , self.num_tasks['all'])

    def testTaskStates(self):
        self.login()
        #Get all active tasks
        result = self.app_client.get('/get_all_active_tasks', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks) , self.num_tasks['active'])

        #Cancel task ID = 2
        result = self.app_client.post('/cancel_task/1', data=dict(
                referrer="TestClient"), headers={'Referer': '/test'}, 
                follow_redirects=True) 


        #Get active tasks, make sure there are none 
        result = self.app_client.get('/get_all_active_tasks', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks) , self.num_tasks['active'])

        #Mark it as finished instead of canceled
        self.app_client.post('/finish_task/1', follow_redirects=True) 

        result = self.app_client.get('/viewtaskjson/1')
        task = ast.literal_eval(result.data)
        self.assertEqual(task['status'], 'completed')

    def testClaimedTasks(self):
        self.login()
        #Get all claimed tasks
        result = self.app_client.get('/get_all_claimed_tasks', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks) , self.num_tasks['claimed'])

    def testTasksForRequestor(self):
        self.login()
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        result = self.app_client.get('/tasks_for_requestor/' + user['id'], follow_redirects=True)

        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks), self.num_tasks['as_requestor'])

    #Same as above, but doesn't require a specified ID
    def testTasksAsRequestor(self):
        self.login()
        result = self.app_client.get('/get_tasks_as_requestor', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks), self.num_tasks['as_requestor'])

    def testTasksForFulfiller(self): 
        self.login()
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        result = self.app_client.get('/tasks_for_fulfiller/' + user['id'], follow_redirects=True)

        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks), self.num_tasks['as_fulfiller'])

    #Same as above, but doesn't require a specified ID
    def testTasksAsFulfiller(self):
        self.login()
        result = self.app_client.get('/get_tasks_as_fulfiller', follow_redirects=True)
        tasks = ast.literal_eval(result.data)['items']
        self.assertEqual(len(tasks), self.num_tasks['as_fulfiller'])


    def testSetOnline(self):
        self.login()
        result = self.app_client.post('/set_online')
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertEqual(user['online'], 'True')

    def testSetOffline(self):
        self.login()
        result = self.app_client.post('/set_offline')
        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertEqual(user['online'], 'False')

    def testGetOnline(self):
        self.login()
        result = self.app_client.get('/get_online')
        self.assertEqual('{\n  "online": true\n}', result.data)

    def testMyFulfillerTasks(self):
        self.login()
        result = self.app_client.get('/my_fulfiller_tasks')

        #Check if the string uses a time zone
        time_regex = re.compile(".*[0-9]+:[0-9]+ (AM|PM) EDT</label>")

        #expected = open('./test_htmls/fulfiller.html', 'w')
        #expected.write(result.data)
        expected = open('./test_htmls/fulfiller.html', 'r')
        for line in result.data.split('\n'):
            test_line = expected.readline().strip()
            if time_regex.match(test_line):
                continue
            self.assertEqual(test_line, line.strip())
        expected.close()

    def testMyRequesterTasks(self):
        self.login()
        result = self.app_client.get('/my_requester_tasks')

        #Check if the string uses a time zone
        time_regex = re.compile(".*[0-9]+:[0-9]+ (AM|PM) EDT</label>")
                        
        #expected = open('./test_htmls/requester.html', 'w')
        #expected.write(result.data)
        expected = open('./test_htmls/requester.html', 'r')
        for line in result.data.split('\n'):
            test_line = expected.readline().strip()
            if time_regex.match(test_line):
                continue
            self.assertEqual(test_line, line.strip())

        expected.close()

    def testViewTaskJSON(self):
        self.login()
        result = self.app_client.get('/viewtaskjson/1')
        expected = {
            "bid": "5.0",
            "delivery_location": "Saybrook",
            "latitude": "41.3121",
            "long_title": "This is a task that will be claimed",
            "longitude": "-72.9277",
            "serialize_requestor_email": "michael.hopkins@yale.edu",
            "short_title": "Claim task",
            "status": "completed",
            "venmo_status": "unpaid"
        }
       # expected = encryption.encrypt_dictionary(expected)
       # expected["status"] = "completed"
       # expected["venmo_status"] = "unpaid"
        task = ast.literal_eval(result.data)
        self.assertEqual(expected, task)

    def testViewTaskDetails(self):
        self.login()
        result = self.app_client.get('/viewtaskdetails/2')

        #Check if the string uses a time zone
        time_regex = re.compile(".*[0-9]+:[0-9]+ (AM|PM) EDT</label>")

        expected = open('./test_htmls/taskdetails.html', 'r')
        for line in result.data.split('\n'):
            test_line = expected.readline().strip()
            if time_regex.match(test_line):
                continue
            self.assertEqual(test_line, line.strip())

        expected.close()

    #Note: Venmo payment left untested as that is mainly sending requests
    #to the Venmo API
    def testVenmoAuth(self):
        self.login()
        with self.app_client.session_transaction() as sess:
            sess['post_venmo_url'] = '/my_requester_tasks'
        result = self.app_client.get('/venmo_auth', query_string=dict(
            access_token='abcdefgh1234567'), headers={'Referer': '/test'})

        current_user = self.app_client.get('/get_user') 
        user = ast.literal_eval(current_user.data)
        self.assertTrue('venmo_token' in user)
        self.assertEqual(user['venmo_token'], encryption.encrypt_string('abcdefgh1234567'))



def addBaseTasks():
    task1dict = {"latitude": 41.3121, "longitude": -72.9277, "short_title": "Claim task", "bid": float(5), \
                 "long_title": "This is a task that will be claimed", "delivery_location": "Saybrook"}
    task2dict = {"latitude": 41.3121, "longitude": -72.9277, "short_title": "Title 2", "bid": float(5), \
                 "long_title": "This is description 2", "delivery_location": "Saybrook"}
    task3dict = {"latitude": 41.3101, "longitude": -72.9257, "short_title": "Title 3", "bid": float(10), \
                 "long_title": "This is description 3", "delivery_location": "There"}
    task4dict = {"latitude": 41.3131, "longitude": -72.9287, "short_title": "Title 4", "bid": float(15), \
                 "long_title": "This is description 4", "delivery_location": "Here"}
    
    task1enc = encryption.encrypt_dictionary(task1dict)
    task2enc = encryption.encrypt_dictionary(task2dict)
    task3enc = encryption.encrypt_dictionary(task3dict)
    task4enc = encryption.encrypt_dictionary(task4dict)
    
    task1 = schema.Task(
        requestor_id=1,
        latitude = task1enc["latitude"],
        longitude = task1enc["longitude"],
        short_title= task1enc["short_title"],
        bid= task1enc["bid"],
        expiration_datetime=datetime.datetime.now() + datetime.timedelta(minutes=6*60),
        long_title= task1enc["long_title"],
        delivery_location= task1enc["delivery_location"],
        status="unassigned")

    task2 = schema.Task(
        requestor_id=1,
        latitude = task2enc["latitude"],
        longitude = task2enc["longitude"],
        short_title= task2enc["short_title"],
        bid= task2enc["bid"],
        expiration_datetime=datetime.datetime.now() + datetime.timedelta(minutes=6*60),
        long_title=task2enc["long_title"],
        delivery_location=task2enc["delivery_location"],
        status="unassigned")

    task3 = schema.Task(
        requestor_id=1,
        latitude = task3enc["latitude"],
        longitude = task3enc["longitude"],
        short_title= task3enc["short_title"],
        bid= task3enc["bid"],
        expiration_datetime=datetime.datetime.now(),
        long_title=task3enc["long_title"],
        delivery_location=task3enc["delivery_location"],
        status="canceled")

    task4 = schema.Task(
        requestor_id=1,
        latitude = task4enc["latitude"],
        longitude = task4enc["longitude"],
        short_title=task4enc["short_title"],
        bid=task4enc["bid"],
        expiration_datetime=datetime.datetime.now(),
        long_title=task4enc["long_title"],
        delivery_location=task4enc["delivery_location"],
        status="expired")

    app.db.session.add(task1) 
    app.db.session.add(task2)
    app.db.session.add(task3) 
    app.db.session.add(task4) 
    app.db.session.commit()


def addBaseUsers():

    user1dict = {"phone":"7703629815", "phone_carrier":"AT&T", "email":"michael.hopkins@yale.edu", \
                 "password":"blah", "venmo_id":"1020501350678528475", "first_name":"Michael", \
                 "last_name":"Hopkins"}

    user2dict = {"phone":"2034420233", "phone_carrier":"AT&T", "email":"miles.richardson@yale.edu", \
                 "password":"blah", "venmo_id":"1020501350678528478", "first_name":"Miles", \
                 "last_name":"Richardson"}

    user1enc = encryption.encrypt_dictionary(user1dict)
    user2enc = encryption.encrypt_dictionary(user2dict)

    user = schema.Account(
        activated=True,
        phone=user1enc["phone"],
        phone_carrier=user1enc["phone_carrier"],
        email=user1enc["email"],
        password=user1enc["password"],
        online=True,
        venmo_id=user1enc["venmo_id"],
        first_name=user1enc["first_name"],
        last_name=user1enc["last_name"])

    user2 = schema.Account(
        activated=True,
        phone=user2enc["phone"],
        phone_carrier=user2enc["phone_carrier"],
        email=user2enc["email"],
        password=user2enc["password"],
        online=True,
        venmo_id=user2enc["venmo_id"],
        first_name=user2enc["first_name"],
        last_name=user2enc["last_name"])

    app.db.session.add(user)
    app.db.session.add(user2)
    app.db.session.commit()




if __name__ == "__main__":
    addBaseUsers()
    addBaseTasks()
    unittest.main()

