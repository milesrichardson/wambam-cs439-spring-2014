from flask import Flask
import sys
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), './templates')

app = Flask(__name__, template_folder=ASSETS_DIR, static_folder=ASSETS_DIR)

if sys.platform == 'win32':
    sys.path.append("wambam\\website");
    sys.path.append("wambam\\api");

else:
    sys.path.append("wambam/website");
    sys.path.append("wambam/api");

import api
import run
