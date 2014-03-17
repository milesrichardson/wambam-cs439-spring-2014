from flask import Flask
import sys
import os

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), './templates')

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), './static')

app = Flask(__name__)

if sys.platform == 'win32':
    sys.path.append("wambam\\website");
    sys.path.append("wambam\\api");

else:
    sys.path.append("wambam/website");
    sys.path.append("wambam/api");

import api
import run
