import unittest
import datetime as dt
from app.models import Stock, StockPoint
from app import app, db
from mock import patch
from pandas import DataFrame, DatetimeIndex

class TestStock(unittest.TestCase):
    
    def setUp(self):
        db.create_all()   # create test database
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')

    def tearDown(self):
        db.drop_all()
        
    def test_db(self):
        ''' using 'TESTING_FLAG' environment variable to know which DB.. There's
        a better way to do this.'''
        assert('tmp/testing.db' in str(db.engine))


    def test_init(self):
        assert(self.stock.symbol == "TSLA")
        assert(self.stock.name == "Tesla Motors Inc")
        assert(self.stock.market == "NASDAQ")

    @patch('app.models.Stock.fetch_ohlc_from_google')
    def test_fetch_all_ohlc_from_google(self,mock_fetch):   
        df = self.stock.fetch_and_save_all_ohlc()
        end= dt.date.today()
        start = end - dt.timedelta(Stock.LOOKBACK_DAYS)
        mock_fetch.assert_called_with(start,end)

    @patch('app.models.DataReader')
    def test_fetch_ohlc_from_google(self, MockDataReader):
        end = dt.date.today()
        start = end - dt.timedelta(days=1)
        df = self.stock.fetch_ohlc_from_google(start, end)
        MockDataReader.assert_called_with("TSLA","google",start,end)

    def test_save_points_creates_new_stock(self):
        assert(Stock.query.count() == 0)
        df = DataFrame()
        self.stock.save_points(df)
        assert(Stock.query.count() == 1)

    def test_save_points_does_not_create_new_stock(self):
        df = DataFrame()
        self.stock.save_points(df)
        assert(Stock.query.count() == 1)
        self.stock.save_points(df)
        assert(Stock.query.count() == 1)

    def test_save_points_creates_new_stockpoint(self): 
        assert(StockPoint.query.count() == 0)
        # Pandas initially creates DatetimeIndices, so replicate it.
        dti1 = DatetimeIndex([dt.date(2014,8,9)])[0]
        df = DataFrame({'Date':[dti1],
                        'Open':[2.],
                        'High':[3.],
                        'Low':[1.],
                        'Close':[2.53],
                        'Volume':[1234567]},
                        index=[0])
        self.stock.save_points(df)
        assert(StockPoint.query.count() == 1)
        assert(len(self.stock.stockpoints) == 1)
        queriedStock = Stock.query.filter(Stock.symbol == 'TSLA').first()
        assert(queriedStock.id == 1)
        queriedStockPoint = StockPoint.query.filter(StockPoint.stock_id == 1).first()
        assert(queriedStockPoint is not None)

    @patch('app.models.Stock.fetch_ohlc_from_google')
    def test_fetch_and_save_missing_ohlc(self, mock_fetch):
        three_days_ago = dt.date.today() - dt.timedelta(days=3)
        four_days_ago = dt.date.today()  - dt.timedelta(days=4)
        dti1 = DatetimeIndex([four_days_ago])[0]
        dti2 = DatetimeIndex([three_days_ago])[0]
        df = DataFrame({'Date':[dti1,dti2],
                        'Open':[2.,3.5],
                        'High':[3.,5.5],
                        'Low':[1.,1.5],
                        'Close':[2.53,4.25],
                        'Volume':[1234567,2345678]},
                        index=[0,1])
        self.stock.save_points(df)
        self.stock.fetch_and_save_missing_ohlc()
        two_days_ago = dt.date.today() - dt.timedelta(days=2)
        one_day_ago = dt.date.today() - dt.timedelta(days=1)
        mock_fetch.assert_called_with(two_days_ago,one_day_ago)

    @patch('app.models.Stock.fetch_and_save_missing_ohlc')
    @patch('app.models.Stock.fetch_and_save_all_ohlc')
    def test_get_dataframe(self, mock_fetch_all, mock_fetch_missing):
        self.stock.get_dataframe()
        assert(mock_fetch_all.called)
        three_days_ago = dt.date.today() - dt.timedelta(days=3)
        four_days_ago = dt.date.today()  - dt.timedelta(days=4)
        dti1 = DatetimeIndex([four_days_ago])[0]
        dti2 = DatetimeIndex([three_days_ago])[0]
        df = DataFrame({'Date':[dti1,dti2],
                        'Open':[2.,3.5],
                        'High':[3.,5.5],
                        'Low':[1.,1.5],
                        'Close':[2.53,4.25],
                        'Volume':[1234567,2345678]},
                        index=[0,1])
        self.stock.save_points(df)
        self.stock.get_dataframe()
        assert(mock_fetch_missing.called)

    def test_load_dataframe_from_db(self):
        two_days_ago = dt.date.today() - dt.timedelta(days=2)
        one_day_ago = dt.date.today() - dt.timedelta(days=1)
        dti1 = DatetimeIndex([two_days_ago])[0]
        dti2 = DatetimeIndex([one_day_ago])[0]
        df = DataFrame({'Date':[dti1,dti2],
                        'Open':[2.,3.5],
                        'High':[3.,5.5],
                        'Low':[1.,1.5],
                        'Close':[2.53,4.25],
                        'Volume':[1234567,2345678]},
                        index=[0,1])
        self.stock.save_points(df)
        df = self.stock.load_dataframe_from_db()
        assert(len(df) == 2)
        assert(df.loc[two_days_ago]['Volume'] == 1234567)
        assert(df.loc[one_day_ago]['Close'] == 4.25)

    ####
    #### Need to mock DataFrame and raise an IOError
    ####

    @patch('app.models.DataReader')
    def test_fetch_ohlc_from_google_fails_gracefully_with_invalid_stock(self, mockDataReader):
        mockDataReader.side_effect = IOError # raised when symbol isn't found
        self.stock.symbol = 'This is an invalid symbol'
        start = end = dt.date.today() - dt.timedelta(days=1)
        df = self.stock.fetch_ohlc_from_google(start,end)
        assert(df is None)

    def test_saving_bad_df_to_database(self):
        assert(Stock.query.count() == 0)
        assert(StockPoint.query.count() == 0)
        dti1 = DatetimeIndex([dt.date(2014,8,9)])[0]
        df = DataFrame({'Date':[dti1],
                        'Open':['-'],
                        'High':['&'],
                        'Low':['^'],
                        'Close':[''],
                        'Volume':[0]},
                        index=[0])
        self.stock.save_points(df)
        assert(StockPoint.query.count() == 0)
        assert(Stock.query.count() == 0)
