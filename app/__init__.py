from flask import Flask
from os import path, getenv

app = Flask(__name__)

#############  Load config files  #############################

if getenv('PRODUCTION_FLAG', None) is not None:
  app.config.from_object('app.config.ProductionConfig')
else:
  app.config.from_object('app.config.DevelopmentConfig')

###############################################################

from app import views 

