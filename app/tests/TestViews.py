from app import app, db
import unittest
from mock import patch

class TestViews(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.app = app.test_client() 

    def tearDown(self):
        db.drop_all()

    @patch('app.models.Stock.find_buy_stocks')
    @patch('app.models.Stock.find_sell_stocks')
    def test_home_page(self, mock_sell, mock_buy):
        rv = self.app.get('/')
        assert('Welcome to ChartFlux' in rv.data)
        assert(mock_buy.called)
        assert(mock_sell.called)

    def test_chart_page(self):
        rv = self.app.get('/chart?symbol=TSLA')
        assert('TSLA' in rv.data)
