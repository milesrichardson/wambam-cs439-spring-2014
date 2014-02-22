from flask import Flask
from flask import request, redirect, url_for
from flask import render_template

app = Flask(__name__)

flask_pos = []
 
@app.route("/")
def hello():
    return render_template('login.html')

@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/login", methods=['POST'])
def login():
    user = request.form['userfield']
    password = request.form['passwordfield']
    return redirect(url_for('home'))

@app.route("/register", methods=['POST'])
def register():
    phone = request.form['phone']
    email = request.form['email']
    password = request.form['password']
    passwordconfirm = request.form['passwordconfirm']
    return redirect(url_for('home'))
      
@app.route("/addtask")
def index():
    return render_template('submittedtask.html')

@app.route("/dotask")
def execute():
    return render_template('taskserver.html')

@app.route("/confirmphone", methods=['POST'])
def confirm():
    phone = request.form['phonenumber']
    return render_template('confirmation.html')

if __name__ == "__main__":
    app.run(debug=True)
