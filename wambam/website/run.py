from flask import Flask
from flask import request
from flask import render_template
from twilio.rest import TwilioRestClient

twaccount = "AC032798eca07124939abd8352c516f86d"
twtoken = "bbc20641c4fdb7e5a0ccc86b4fdefcfe"
twilio_client = TwilioRestClient(twaccount, twtoken)

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
    message = twilio_client.messages.create(to="+1"+phone, from_="+1954607-3879", body="Confirmed for WAMBAM!")
    return render_template('confirmation.html')

if __name__ == "__main__":
    app.run(debug=True)
