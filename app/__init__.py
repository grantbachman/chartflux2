from flask import Flask
from os import path, getenv
from flask.ext.sqlalchemy import SQLAlchemy
app = Flask(__name__)

#############  Load config files  #############################

if getenv('PRODUCTION_FLAG', None) is not None:
    app.config.from_object('app.config.ProductionConfig')
elif getenv('TESTING_FLAG', None) is not None:
    app.config.from_object('app.config.TestingConfig')
else:
    app.config.from_object('app.config.DevelopmentConfig')

###############################################################

db = SQLAlchemy(app)

from app import views 

