import unittest
import datetime as dt
from app.models import Stock, StockPoint, RSI, MACD
from app import db
from pandas import DataFrame, DatetimeIndex

class TestMACD(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')

    def tearDown(self):
        db.drop_all()

    def test_MACD_columns_are_added(self):
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
        df = self.stock.load_dataframe_from_db()
        df = MACD(df).df
        exception_raised = False
        try:
            macd = df['MACD']
            macd_signal = df['MACD-Signal']
        except:
            exception_raised = True
        assert(exception_raised == False)

    def test_MACD_values_are_saved(self):
        days = 30
        close = [1,2,3,4,5,6,7,8,9,13,15,1,23,19,12,15,18,19,19,20,23,21,23,24,27,24,29,31,32,30]
        dtLst = DatetimeIndex([dt.date.today() - dt.timedelta(days=days) + dt.timedelta(days=i) for i in range(days)])
        dtLst = list(dtLst)
        df = DataFrame({'Date': dtLst,
                        'Open':[1] * days,
                        'High':[1] * days,
                        'Low':[1] * days,
                        'Close':close,
                        'Adj Close':close,
                        'Volume':[1000000] * days},
                        index=range(days))
        df2 = MACD(df).df
        self.stock._save_dataframe(df)
        assert(len(self.stock.stockpoints) == days)
        self.stock.calculate_indicators()
        assert(self.stock.stockpoints[-1].macd is not None)
        assert(self.stock.stockpoints[-1].macd_signal is not None)
       

class TestRSI(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')

    def tearDown(self):
        db.drop_all()

    def test_RSI_returns_correct_values(self):
        # same number of up days and down days. RSI should be 50
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
        df = self.stock.load_dataframe_from_db()
        df = RSI(df).df
        assert(df.ix[-1]['RSI'] == 50)
    
    def test_RSI_updates_stockPoint_rows(self):
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
        assert(len(self.stock.stockpoints) == 14)
        self.stock.calculate_indicators()
        assert(self.stock.stockpoints[0].rsi is None)
        assert(self.stock.stockpoints[-1].rsi is not None)

    def test_RSI_save_indicators_doesnt_save_bad_data(self):
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
        df = self.stock.load_dataframe_from_db()
        df = RSI(df).df
        df.reset_index(inplace=True)
        df['RSI'][:] = "Bad data"
        self.stock._save_indicators(df)
        assert(self.stock.stockpoints[-1].rsi is None)

    def test_RSI_recommends_stock_to_sell(self):
        # close: today --> x days ago
        close = [14,13,12,11,10,9,8,7,6,5,4,3,2,1]
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
        self.stock.calculate_indicators()
        lst = RSI.find_sell_stocks()
        assert(isinstance(lst,list))
        assert(len(lst) != 0)
        assert(lst[0][1].symbol == 'TSLA')

    def test_RSI_recommends_stock_to_buy(self):
        # close: today --> x days ago
        close = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
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
        self.stock.calculate_indicators()
        lst = RSI.find_buy_stocks()
        assert(isinstance(lst,list))
        assert(len(lst) != 0)
        assert(lst[0][1].symbol == 'TSLA')

