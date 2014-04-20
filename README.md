Use:

export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments

on MAC OSX before doing a pip install -r requirements.txt. Otherwise psycopg2 will fail to build 
