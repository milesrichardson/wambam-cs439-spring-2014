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

@app.route("/working")
def working():
    return render_template('working.html')

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
    return render_template('addtask.html')

@app.route("/submittask", methods=['POST'])
def submit():
    title = request.form['title']
    location = request.form['deliveryloc']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']
    return redirect(url_for('confirm'))

@app.route("/dotask")
def execute():
    return render_template('taskserver.html')

@app.route("/confirmWamBam", methods=['POST'])
def wambam():
    title = request.form['title']
    location = request.form['location']
    bid = request.form['bid']
    expiration = request.form['expiration']
    description = request.form['description']
    email = request.form['description']
    return redirect(url_for('home'))

@app.route("/confirm")
def confirm():
    return render_template('confirmation.html')

if __name__ == "__main__":
    app.run(debug=True)
