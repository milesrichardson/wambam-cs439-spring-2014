from flask import Flask
from flask import request
from flask import render_template
app = Flask(__name__)

flask_pos = []
 
@app.route("/")
def hello():
    return render_template('index.html')
      
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
