from flask import Flask
from os import path, getenv
from flask.ext.sqlalchemy import SQLAlchemy
app = Flask(__name__)
import logging

#############  Load config files  #############################

if getenv('PRODUCTION_FLAG', None) is not None:
    app.config.from_object('app.config.production_config')
elif getenv('TESTING_FLAG', None) is not None:
    app.config.from_object('app.config.testing_config')
else:
    app.config.from_object('app.config.development_config')

###############################################################

db = SQLAlchemy(app)

from app import views 

