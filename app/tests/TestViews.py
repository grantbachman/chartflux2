from app import app, db
import unittest
from app.models import Stock
from mock import patch
from pandas import DataFrame, DatetimeIndex
import datetime as dt

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

    def test_home_page_404(self):
        rv = self.app.get('/')
        assert('404' in rv.data)

    def test_chart_page_404(self):
        ''' There's no data, so it should 404'''
        rv = self.app.get('/chart?symbol=TSLA')
        assert('404' in rv.data)

    def test_chart_page_with_data_no_404(self):
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        dti1 = DatetimeIndex([dt.date(2014,8,9)])[0]
        df = DataFrame({'Date':[dti1],
                        'Open':[2.],
                        'High':[3.],
                        'Low':[1.],
                        'Close':[2.53],
                        'Adj Close':[2.53],
                        'Volume':[1234567]},
                        index=[0])
        self.stock._save_dataframe(df)
        rv = self.app.get('/chart?symbol=TSLA')
        assert('404' not in rv.data)

    def test_NA_fields(self):
        ''' With only one data point, there won't exist an RSI value '''
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        dti1 = DatetimeIndex([dt.date(2014,8,9)])[0]
        df = DataFrame({'Date':[dti1],
                        'Open':[2.],
                        'High':[3.],
                        'Low':[1.],
                        'Close':[2.53],
                        'Adj Close':[2.53],
                        'Volume':[1234567]},
                        index=[0])
        self.stock._save_dataframe(df)
        rv = self.app.get('/chart?symbol=TSLA')
        assert('N/A' in rv.data)





