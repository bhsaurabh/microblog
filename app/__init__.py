# Simple init script for flask app
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')  # read-in configuration file

from app import views
