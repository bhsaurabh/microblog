# Simple init script for flask app
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir
import os
from momentjs import momentjs

app = Flask(__name__)
app.jinja_env.globals['momentjs'] = momentjs
app.config.from_object('config')  # read-in configuration file
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from app import views, models
