from flask import Flask
import sys

app = Flask(__name__)

if sys.platform == 'win32':
    sys.path.append("wambam\\website");
    sys.path.append("wambam\\api");

else:
    sys.path.append("wambam/website");
    sys.path.append("wambam/api");

import api
import run
