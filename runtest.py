import os

postgres = None
if "DATABASE_URL" in os.environ:
    postgres = os.environ["DATABASE_URL"]
    del os.environ["DATABASE_URL"]

from wambam import app

if postgres is not None:
    os.environ["DATABASE_URL"] = postgres


import unittest

import ast
port = int(os.environ.get('PORT', 5000))


class TestWambam(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app_client = app.test_client()

        #There are 4 tasks in the DB initially. 
        #Two are unclaimed. AddClaimTask is the first test which will
        #claim a task. AddSubmittedTask will create a new task, so
        #the num_tasks variable reflects these stats for the other tests
        self.num_tasks = {'all':5, 
                          'active':2,
                          'claimed':1,
                          'as_requestor':4,
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

        #This'll be tested in claim task later

    #Forced to happen first
    def testAddSubmitTask(self):
        self.login()
        with self.app_client.session_transaction() as sess:
            sess['lat'] = 41.3084304
            sess['lng'] = -72.9284356
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
        result = self.app_client.post('/cancel_task/2', data=dict(
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

        expected = open('./test_htmls/fulfiller.html', 'r')
        for line in result.data.split('\n'):
            test_line = expected.readline().strip()
            if test_line == "<label>Sunday 03:50 AM EDT</label>":
                continue
            self.assertEqual(test_line.strip(), line.strip())

        expected.close()

    def testMyRequesterTasks(self):
        self.login()
        result = self.app_client.get('/my_requester_tasks')
        time_strings = ["<label>Sunday 04:03 AM EDT</label>",
                        "<label>Sunday 10:33 PM EDT</label>",
                        "<label>10:33 PM EDT</label>"]
                        

        expected = open('./test_htmls/requester.html', 'r')
        for line in result.data.split('\n'):
            test_line = expected.readline().strip()
            if test_line in time_strings:
                continue
            self.assertEqual(test_line.strip(), line.strip())

        expected.close()

    def testViewTaskJSON(self):
        self.login()
        result = self.app_client.get('/viewtaskjson/1')
        print result.data



    ##TODO FEEDBACK TESTS (285 in api.py)
    ##TODO MY VIEWTASKJSON/DETAILS TESTS (780ish in api.py)
    ##TODO VENMO TESTS (850ish in api.py)


if __name__ == "__main__":
    unittest.main()

