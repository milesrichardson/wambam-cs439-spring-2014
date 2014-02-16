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
    print render_template('submittedtask.html')

if __name__ == "__main__":
    app.run(debug=True)
