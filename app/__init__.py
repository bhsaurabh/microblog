# Simple init script for flask app
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')  # read-in configuration file
db = SQLAlchemy(app)

from app import views, models
