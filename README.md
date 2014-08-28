WHAT THIS IS
=====

This is the code for our CS 439 group project, "WamBam". Wambam is "uber for tasks". Drop a pin, fill task details, find someone to fulfill it.

Team Members: (W)ill Childs-Klein, (A)dit Sinha, (M)iles Richardson, (B)randon Smith, (A)ayush Upadhyay, (M)ichael Hopkins

continue
===

-Our code running live can be viewed at wambam.net
-If you want to run the code locally, when you register for an account on WamBam! and have to 
 activate your account, you will need to change the base URL from wambam.herokuapp.com to localhost:5000.

Use:

export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments

on MAC OSX before doing a pip install -r requirements.txt. Otherwise psycopg2 will fail to build 

To run the code coverage tool, use:

coverage run --source=wambam/api,wambam/website runtest.py
coverage html

Then navigate to htmlcov/index.html and you can view stats/see code. 

Current directory structure:

./
    requirements.txt - list of project dependecies
    runtest.py - From the root directory, "python runtest.py" runs the test suite. This test suite
                 contains unit tests, regression tests, and integration tests.
    runserver.py - From the root directoy, "python runserver.py" runs WamBam! locally at 
                   localhost:5000
    htmlcov/ - great details on code coverage
    
    /wambam
        api/ - backend server code
        mockups/ - initial design mockups for WamBam!
        templates/ - html code for frontend 
        static/ - javascript, pictures, and css
        website/ - basic endpoints of backend server code

Basic WamBam! workflows:
-Register on the home page with a Yale email address
-Click the activation link in the email sent to you.
-Request a task
    -Drop a pin on the map.
    -Click "Get it done!"
    -Fill in the details of your task and submit
    -Receive confirmation text from WamBam!
    -Wait until someone claims task.
    -Receive text message alert that someone has claimed your task with their phone number to get in touch.
    -After task has been fulfilled, requester can navigate to "My History" page and pay with Venmo 
     optionally.
-Fulfill a task
    -Click "I want to work"
    -Click on a google maps pin
    -View the details and claim task
    -Text fulfiller that you are on it.
    -Rate requester's service and receive payment (optionally through Venmo if you have signed up)
     through the "My History tab" Task is done after rating.

Key WamBam! Features
  -Data encryption on the backend
  -Venmo payment integration
  -Mobile obtimized and desktop optimized websites.
  -Optional text message alerts.
