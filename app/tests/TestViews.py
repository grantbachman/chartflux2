from app import app, db
import unittest
from app.models import Stock
from mock import patch
from pandas import DataFrame, DatetimeIndex
import datetime as dt
import StockFactory as SF

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

    def test_chart_page_404(self):
        # There's no data, so it should 404
        rv = self.app.get('/chart?symbol=TSLA')
        assert('404' in rv.data)

    def test_chart_page_with_data_no_404(self):
        self.stock = SF.build_stock()
        df = SF.build_dataframe()
        self.stock._save_dataframe(df)
        rv = self.app.get('/chart?symbol=TSLA')
        assert('404' not in rv.data)
