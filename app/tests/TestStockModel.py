import unittest
import datetime as dt
from datetime import date
from app.models import Stock, StockPoint
from app import app, db
from mock import patch
from pandas import DataFrame, DatetimeIndex

class TestStockPoint(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        close = [1,2,3,4,5,6,7,7,6,5,4,3,2,1]
        days = 14
        # Create a dataframe for the past 15 days
        dtLst = DatetimeIndex([dt.date.today() - dt.timedelta(days=i) for i in range(days)])
        df = DataFrame({'Date':list(dtLst),
                        'Open':[1] * days,
                        'High':[1] * days,
                        'Low':[1] * days,
                        'Close':close,
                        'Adj Close':close,
                        'Volume':[1000000] * days},
                        index=range(days))
        self.stock._save_dataframe(df)

    def tearDown(self):
        db.drop_all()

    def test_save_dataframe_creates_new_stockpoints(self):
        assert(StockPoint.query.filter(Stock.id == 1).count() == 14)

    def test_last_known_date(self):
        assert(StockPoint.query.count() == 14)
        assert(StockPoint.last_known_date() == dt.date.today())
    
    def test_stockpoint_repr(self):
        print self.stock.stockpoints[0]
        assert("<StockPoint(id='14', stock_id='1'" in self.stock.stockpoints[0].__repr__())


class TestStock(unittest.TestCase):
    
    def setUp(self):
        db.create_all()   # create test database
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')

    def tearDown(self):
        db.drop_all()
        
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

    def test_stock_repr(self):
        assert(self.stock.__repr__() == "<Stock(id='None', symbol='TSLA', name='Tesla Motors Inc', market='NASDAQ')>")

    def test_init(self):
        assert(self.stock.symbol == "TSLA")
        assert(self.stock.name == "Tesla Motors Inc")
        assert(self.stock.market == "NASDAQ")

    def test_load_dataframe_from_db(self):
        today = dt.date.today()
        dti = DatetimeIndex([today])[0]
        df = DataFrame({'Date':[dti],
                        'Open':[2.],
                        'High':[3.],
                        'Low':[1.],
                        'Close':[2.5],
                        'Adj Close':[2.5],
                        'Volume':[1234567]},
                        index=[0])
        self.stock._save_dataframe(df)
        df = self.stock.load_dataframe_from_db()
        assert(df.loc[today]['Open'] == 2)
        assert(df.loc[today]['High'] == 3)
        assert(df.loc[today]['Low'] == 1)
        assert(df.loc[today]['Close'] == 2.5)
        assert(df.loc[today]['Adj Close'] == 2.5)
        assert(df.loc[today]['Volume'] == 1234567)

    @patch('app.models.Stock.fetch_ohlc_from_yahoo')
    def test_fetch_all_ohlc_from_yahoo(self,mock_fetch):   
        df = self.stock.fetch_and_save_all_ohlc()
        end= dt.date.today()
        start = end - dt.timedelta(Stock.LOOKBACK_DAYS)
        mock_fetch.assert_called_with(start,end)

    @patch('app.models.DataReader')
    def test_fetch_ohlc_from_yahoo(self, MockDataReader):
        end = dt.date.today()
        start = end - dt.timedelta(days=1)
        df = self.stock.fetch_ohlc_from_yahoo(start, end)
        MockDataReader.assert_called_with("TSLA","yahoo",start,end)

    def test_save_dataframe_creates_new_stock(self):
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
        date1 = dt.date(2014,10,6)
        date2 = dt.date(2014,10,7)
        dti1 = DatetimeIndex([date1])[0]
        dti2 = DatetimeIndex([date2])[0]
        df = DataFrame({'Date':[dti1,dti2],
                        'Open':[2.,3.5],
                        'High':[3.,5.5],
                        'Low':[1.,1.5],
                        'Close':[2.53,4.25],
                        'Adj Close':[2.53,4.25],
                        'Volume':[1234567,2345678]},
                        index=[0,1])
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
                                                 adj_close=1,volume=10))
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
        ''' Should only save points with valid data '''
        assert(Stock.query.count() == 0)
        assert(StockPoint.query.count() == 0)
        dti1 = DatetimeIndex([dt.date(2014,8,9)])[0]
        dti2 = DatetimeIndex([dt.date(2014,8,10)])[0]
        df = DataFrame({'Date':[dti1, dti2],
                        'Open':[2, '-'],
                        'High':[3, '-'],
                        'Low':[1, '-'],
                        'Close':[2,'-'],
                        'Adj Close':[2,''],
                        'Volume':[1,0]},
                        index=[0,1])
        self.stock._save_dataframe(df)
        assert(StockPoint.query.count() == 1)
        assert(Stock.query.count() == 1)
