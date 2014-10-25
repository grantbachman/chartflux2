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

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/testing.db'
    TESTING = True
    DEBUG = True

class DevelopmentConfig(Config):
    username = 'chartflux'
    password = 'chartflux_password'
    host = 'localhost'
    name = 'chartflux'
    port = '5432'
    SQLALCHEMY_DATABASE_URI = 'postgresql://' + username + ':' + \
                                password + '@' + host + '/' + name
    DEBUG = True


