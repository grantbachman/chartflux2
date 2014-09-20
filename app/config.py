import os

class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
    username = str(os.getenv('DB_USERNAME'))
    password = str(os.getenv('DB_PASSWORD'))
    host = str(os.getenv('DB_HOST'))
    name = str(os.getenv('DB_NAME'))
    port = str(os.getenv('DB_PORT', '5432'))
    # postgresql://username:password@host/dbname
    SQLALCHEMY_DATABASE_URI = 'postgresql://' + username + ':' + \
                                password + '@' + host + '/' + name

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'
    DEBUG = True
    TESTING = True

