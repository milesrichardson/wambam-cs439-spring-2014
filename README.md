Use:

export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments

on MAC OSX before doing a pip install -r requirements.txt. Otherwise psycopg2 will fail to build 

To run the code coverage tool, use:

coverage run --source=wambam/api,wambam/website runtest.py
coverage html

Then navigate to htmlcov/index.html and you can view stats/see code. 


