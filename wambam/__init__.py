from flask import Flask
import sys

app = Flask(__name__)

sys.path.append("wambam\\website");
sys.path.append("wambam\\api");
import api
import run
