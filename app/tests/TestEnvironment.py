import unittest
from mock import patch
import os
import app

class TestTestingEnvironment(unittest.TestCase):
  
    def setUp(self):
        os.environ['TESTING_FLAG']='1'
        reload(app)
        self.db = app.db

    def tearDown(self):
        del os.environ['TESTING_FLAG']

    def test_using_correct_db_engine(self):
        assert('sqlite' in repr(self.db))

class TestProductionConfig(unittest.TestCase):

    def setUp(self):
        os.environ['PRODUCTION_FLAG']='1'
        reload(app)
        self.db = app.db

    def tearDown(self):
        del os.environ['PRODUCTION_FLAG']

    def test_using_correct_db_engine(self):
        assert('postgres' in repr(self.db))

class TestDevelopmentConfig(unittest.TestCase):

    def setUp(self):
        del os.environ['TESTING_FLAG']
        reload(app)
        self.db = app.db

    def tearDown(self):
        pass

    def test_using_correct_db_engine(self):
        print self.db
        assert('postgresql://chartflux:chartflux_password' in repr(self.db))
