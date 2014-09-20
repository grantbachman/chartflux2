from app import app
import unittest
class TestViews(unittest.TestCase):

    def setUp(self):
       self.app = app.test_client() 

    def test_home_page(self):
        rv = self.app.get('/')
        assert('Welcome to ChartFlux' in rv.data)

    def test_chart_page(self):
        rv = self.app.get('/chart?symbol=TSLA')
        assert('TSLA' in rv.data)
