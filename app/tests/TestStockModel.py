import unittest
import datetime as dt
from datetime import date
from app.models import Stock, StockPoint, Signal
from app import app, db
from mock import patch
import pandas as pd
from pandas import DataFrame, DatetimeIndex
import StockFactory as SF

class TestStockPoint(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()
        df = SF.build_dataframe(days=10)
        self.stock._save_dataframe(df)

    def tearDown(self):
        db.drop_all()

    def test_save_dataframe_creates_new_stockpoints(self):
        assert(StockPoint.query.filter(Stock.id == 1).count() == 10)

    def test_last_known_date(self):
        ''' last_known_date() should return the date of last point '''
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

    def test_stock_repr(self):
        assert(self.stock.__repr__() == "<Stock(id='None', symbol='TSLA', name='Tesla Motors Inc', market='NASDAQ')>")

    def test_init(self):
        assert(self.stock.symbol == "TSLA")
        assert(self.stock.name == "Tesla Motors Inc")
        assert(self.stock.market == "NASDAQ")

    def test_find_buy_stocks(self):
        ''' Stock.find_buy_stocks() should only return Stocks with 2 or
        more non-expired signals (this will probably change later) '''
        signal_1, signal_2, signal_3, signal_4 = Signal(), Signal(), Signal(), Signal()
        # Signal 1 should qualify
        signal_1.expiration_date = dt.date.today() + dt.timedelta(days=1)
        signal_1.is_buy_signal = True
        # Signal 2 should qualify
        signal_2.expiration_date = dt.date.today()
        signal_2.is_buy_signal = True
        # Signal 3 should not qualify since it's not a buy signal
        signal_3.expiration_date = dt.date.today()
        signal_3.is_buy_signal = False
        # Signal 3 should not qualify since it's expired
        signal_4.expiration_date = dt.date.today() - dt.timedelta(days=1)
        signal_4.is_buy_signal = True
        self.stock.signals.append(signal_1)
        self.stock.signals.append(signal_2)
        self.stock.signals.append(signal_3)
        self.stock.signals.append(signal_4)
        db.session.add(self.stock)
        db.session.commit()
        buy_list = Stock.find_buy_stocks()
        print buy_list
        assert(buy_list[0][0] == 1)  # assert Stock.id == 1
        assert(buy_list[0][1] == 2)  # assert there are exactly 2 signals found

    def test_find_sell_stocks(self):
        ''' Stock.find_sell_stocks() should only return Stock IDs with 2 or
        more non-expired signals (this will probably change later) '''
        signal_1, signal_2, signal_3, signal_4 = Signal(), Signal(), Signal(), Signal()
        # Signal 1 should qualify
        signal_1.expiration_date = dt.date.today() + dt.timedelta(days=1)
        signal_1.is_buy_signal = False
        # Signal 2 should qualify
        signal_2.expiration_date = dt.date.today()
        signal_2.is_buy_signal = False
        # Signal 3 should not qualify since it's not a sell signal
        signal_3.expiration_date = dt.date.today()
        signal_3.is_buy_signal = True
        # Signal 4 should not qualify since it's expired
        signal_4.expiration_date = dt.date.today() - dt.timedelta(days=1)
        signal_4.is_buy_signal = False
        self.stock.signals.append(signal_1)
        self.stock.signals.append(signal_2)
        self.stock.signals.append(signal_3)
        self.stock.signals.append(signal_4)
        db.session.add(self.stock)
        db.session.commit()
        sell_list = Stock.find_sell_stocks()
        print sell_list
        assert(sell_list[0][0] == 1)  # assert Stock.id == 1
        assert(sell_list[0][1] == 2)  # assert there are exactly 2 signals found

    def test_signals_are_ordered_properly(self):
        ''' The first signal should be the one with the latest expiration date '''
        signal_1, signal_2, signal_3 = Signal(), Signal(), Signal()
        signal_1.expiration_date = dt.date.today()+dt.timedelta(days=3)
        signal_1.is_buy_signal = True
        signal_2.expiration_date = dt.date.today()+dt.timedelta(days=1)
        signal_2.is_buy_signal = True
        signal_3.expiration_date = dt.date.today()+dt.timedelta(days=5)
        signal_3.is_buy_signal = True
        self.stock.signals.append(signal_1)
        self.stock.signals.append(signal_2)
        self.stock.signals.append(signal_3)
        db.session.add(self.stock)
        print self.stock.signals
        # signals aren't re-ordered until the commit, unless
        # reorder_on_append is set
        db.session.commit()
        print self.stock.signals
        assert(self.stock.signals[0] == signal_3)

    def test_save_dataframe_creates_new_stock(self):
        ''' When a Stock doesn't exist, a new Stock object should be 
        created and saved.
        ''' 
        assert(Stock.query.count() == 0)
        df = DataFrame()
        self.stock._save_dataframe(df)
        assert(Stock.query.count() == 1)

    def test_save_dataframe_does_not_create_new_stock(self):
        ''' When a Stock already exists, no new Stock object should be
        created.
        '''
        df = DataFrame()
        assert(Stock.query.count() == 0)
        self.stock._save_dataframe(df)
        assert(Stock.query.count() == 1)
        self.stock._save_dataframe(df)
        assert(Stock.query.count() == 1)


    def test_load_dataframe_from_db(self):
        ''' When loading a dataframe, all fields our model knows about
        should be loaded, including RSI/MACD/moving averages, etc.
        '''
        today = dt.date.today()
        self.stock.stockpoints.append(StockPoint(today, 1.5, 3.17, 1.21, 
                                                 1.76, 1.76, 123456, 30.14,
                                                 1.21, macd_signal=None))
        db.session.commit()
        
        df = self.stock.load_dataframe_from_db()
        assert(df.loc[today]['Open'] == 1.5)
        assert(df.loc[today]['High'] == 3.17)
        assert(df.loc[today]['Low'] == 1.21)
        assert(df.loc[today]['Close'] == 1.76)
        assert(df.loc[today]['Adj Close'] == 1.76)
        assert(df.loc[today]['Volume'] == 123456)
        assert(df.loc[today]['RSI'] == 30.14)
        assert(df.loc[today]['MACD'] == 1.21)
        assert(pd.isnull((df.loc[today]['MACD-Signal'])))

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
        print df
        assert(StockPoint.query.count() == 2)

    def test_update_dataframe(self):
        ''' Should update the RSI, MACD, MACD-Signal '''
        df = SF.build_dataframe(values={'RSI':[1],'MACD':[2],'MACD-Signal':[3]})
        self.stock._save_dataframe(df) 
        df['RSI'] = 4
        df['MACD'] = 5
        df['MACD-Signal'] = 6
        self.stock.update_dataframe(df)
        assert(self.stock.stockpoints[0].rsi == 4)
        assert(self.stock.stockpoints[0].macd == 5)
        assert(self.stock.stockpoints[0].macd_signal == 6)
