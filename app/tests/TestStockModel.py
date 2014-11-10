import unittest
import datetime as dt
from datetime import date
from app.models import Stock, StockPoint
from app import app, db
from mock import patch
from pandas import DataFrame, DatetimeIndex
import StockFactory as SF

class TestStockPoint(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()
        df = SF.build_dataframe()
        self.stock._save_dataframe(df)

    def tearDown(self):
        db.drop_all()

    def test_save_dataframe_creates_new_stockpoints(self):
        assert(StockPoint.query.filter(Stock.id == 1).count() == 10)

    def test_last_known_date(self):
        assert(StockPoint.query.count() == 10)
        assert(StockPoint.last_known_date() == dt.date.today())
    
    def test_stockpoint_repr(self):
        print self.stock.stockpoints[0]
        assert("<StockPoint(id='1', stock_id='1'" in self.stock.stockpoints[0].__repr__())


class TestStock(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')

    def tearDown(self):
        db.drop_all()
        
    '''
    @patch('app.models.RSI.find_buy_stocks')
    @patch('app.models.MACD.find_buy_stocks')
    def test_find_buy_stocks(self, macd_buy, rsi_buy):
        Stock.find_buy_stocks()
        assert(macd_buy.called)
        assert(rsi_buy.called)

    @patch('app.models.RSI.find_sell_stocks')
    @patch('app.models.MACD.find_sell_stocks')
    def test_find_sell_stocks(self, macd_sell, rsi_sell):
        Stock.find_sell_stocks()
        assert(macd_sell.called)
        assert(rsi_sell.called)
    '''

    def test_stock_repr(self):
        assert(self.stock.__repr__() == "<Stock(id='None', symbol='TSLA', name='Tesla Motors Inc', market='NASDAQ')>")

    def test_init(self):
        assert(self.stock.symbol == "TSLA")
        assert(self.stock.name == "Tesla Motors Inc")
        assert(self.stock.market == "NASDAQ")

    def test_load_dataframe_from_db(self):
        today = dt.date.today()
        df = SF.build_dataframe(days=1)
        self.stock._save_dataframe(df)
        df = self.stock.load_dataframe_from_db()
        assert(df.loc[today]['Open'] == 1)
        assert(df.loc[today]['High'] == 1)
        assert(df.loc[today]['Low'] == 1)
        assert(df.loc[today]['Close'] == 1)
        assert(df.loc[today]['Adj Close'] == 1)
        assert(df.loc[today]['Volume'] == 1)

    @patch('app.models.Stock.fetch_ohlc_from_yahoo')
    def test_fetch_all_ohlc_from_yahoo(self,mock_fetch):   
        df = self.stock.fetch_and_save_all_ohlc()
        end = dt.date.today()
        start = end - dt.timedelta(Stock.LOOKBACK_DAYS)
        mock_fetch.assert_called_with(start,end)

    @patch('app.models.DataReader')
    def test_fetch_ohlc_from_yahoo(self, MockDataReader):
        end = dt.date.today()
        start = end - dt.timedelta(days=1)
        df = self.stock.fetch_ohlc_from_yahoo(start, end)
        MockDataReader.assert_called_with("TSLA","yahoo",start,end)

    def test_save_dataframe_creates_new_stock(self):
        print Stock.query.all()
        assert(Stock.query.count() == 0)
        df = DataFrame()
        self.stock._save_dataframe(df)
        assert(Stock.query.count() == 1)

    def test_save_dataframe_does_not_create_new_stock(self):
        df = DataFrame()
        assert(Stock.query.count() == 0)
        self.stock._save_dataframe(df)
        assert(Stock.query.count() == 1)
        self.stock._save_dataframe(df)
        assert(Stock.query.count() == 1)

    @patch('app.models.today')
    @patch('app.models.Stock.fetch_ohlc_from_yahoo')
    def test_fetch_and_save_missing_ohlc(self, mock_fetch, mock_today):
        mock_today.return_value = dt.date(2014,10,10)
        df = SF.build_dataframe(end_date=dt.date(2014,10,7))
        self.stock._save_dataframe(df)
        self.stock.fetch_and_save_missing_ohlc()
        date3 = dt.date(2014,10,8)
        date4 = dt.date(2014,10,9)
        mock_fetch.assert_called_with(date3, date4)

    @patch('app.models.Stock.fetch_and_save_missing_ohlc')
    @patch('app.models.Stock.fetch_and_save_all_ohlc')
    def test_get_dataframe(self, mock_fetch_all, mock_fetch_missing):
        self.stock.get_dataframe()
        assert(mock_fetch_all.called)
        self.stock.stockpoints.append(StockPoint(date=dt.date.today,
                                                 open=1,high=2,low=1,close=1,
                                                 adj_close=1,volume=1))
        self.stock.get_dataframe()
        assert(mock_fetch_missing.called)

    @patch('app.models.DataReader')
    def test_fetch_ohlc_from_yahoo_fails_gracefully_with_invalid_stock(self, mockDataReader):
        mockDataReader.side_effect = IOError # raised when symbol isn't found
        self.stock.symbol = 'This is an invalid symbol'
        start = end = dt.date.today() - dt.timedelta(days=1)
        df = self.stock.fetch_ohlc_from_yahoo(start,end)
        assert(df is None)

    def test_saving_bad_df_to_database(self):
        ''' Should only save the two points with valid data '''
        assert(StockPoint.query.count() == 0)
        df = SF.build_dataframe(values={'Open':['-',1,2]})
        self.stock._save_dataframe(df)
        assert(StockPoint.query.count() == 2)
