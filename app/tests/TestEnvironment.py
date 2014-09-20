import unittest
from mock import patch
import app
import os

class TestEnvironment(unittest.TestCase):

    def test_app_is_initialized(self):
        assert(app.app is not None)

    def test_db_is_initialized(self):
        assert(app.db is not None)


    '''
    TODO: Learn how to test a module's __init__.py
    
    @patch('app.config.DevelopmentConfig')
    @patch('app.config.ProductionConfig')
    def test_is_not_production(self, MockProductionConfig,
                               MockDevelopmentConfig):
        testapp = app.test_client()
        assert not MockProductionConfig.called
        assert MockDevelopmentConfig.called
    '''
