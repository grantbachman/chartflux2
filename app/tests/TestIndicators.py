import unittest
import datetime as dt
from app.models import Stock, StockPoint, Signal, RSI, RSISignal, MACD
from app.models import MACDSignalCross, MACDCenterCross, SMA50PriceCross
from app.models import SMA200PriceCross, FiftyTwoWeekSignal
from app import db
from pandas import DataFrame, DatetimeIndex, isnull
from decimal import Decimal
import StockFactory as SF
    
class Test52Week(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_buy_signal_triggers(self):
        df = SF.build_dataframe(values={'52-Week-High':[3,3.01],
                                        '52-Week-Low':[1,1]})
        signal = FiftyTwoWeekSignal(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)
        assert(signal.description is not None)

    def test_sell_signal_triggers(self):
        df = SF.build_dataframe(values={'52-Week-High':[3,3],
                                        '52-Week-Low':[1,.99]})
        signal = FiftyTwoWeekSignal(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)
        assert(signal.description is not None)

class TestSMAPrice200Cross(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_buy_signal_triggers(self):
        df = SF.build_dataframe(values={'Adj Close':[1]*50 + [3],
                                        'SMA-200':[2]*51})
        signal = SMA200PriceCross(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)
        assert(signal.description is not None)

    def test_sell_signal_triggers(self):
        df = SF.build_dataframe(values={'Adj Close':[3]*50 + [1],
                                        'SMA-200':[2]*51})
        signal = SMA200PriceCross(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)
        assert(signal.description is not None)

    def test_no_signal_triggers(self):
        df = SF.build_dataframe(values={'Adj Close':[3]*51,
                                        'SMA-200':[2]*51})
        signal = SMA200PriceCross(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == False)
        assert(signal.is_buy_signal == None)
        assert(signal.description is None)

class TestSMAPrice50Cross(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_buy_signal_triggers(self):
        df = SF.build_dataframe(values={'Adj Close':[1]*10 + [3],
                                        'SMA-50':[2]*11})
        signal = SMA50PriceCross(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)
        assert(signal.description is not None)

    def test_sell_signal_triggers(self):
        df = SF.build_dataframe(values={'Adj Close':[3]*10 + [1],
                                        'SMA-50':[2]*11})
        signal = SMA50PriceCross(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)
        assert(signal.description is not None)

    def test_no_signal_triggers(self):
        df = SF.build_dataframe(values={'Adj Close':[3]*11,
                                        'SMA-50':[2]*11})
        signal = SMA50PriceCross(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == False)
        assert(signal.is_buy_signal == None)
        assert(signal.description is None)

class TestMACD(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.df = SF.build_dataframe(values={'Adj Close':[45.15, 46.26, 46.5,
                                                          46.23, 46.08, 46.03,
                                                          46.83, 47.69, 47.54,
                                                          49.25, 49.23, 48.2,
                                                          47.57, 47.61, 48.08,
                                                          47.21, 46.76]})

    def tearDown(self):
        db.drop_all()

    def test_MACD_correctness(self):    
        ''' I'll do this later, but I'm not too concerned right now. '''
        pass

class TestMACDCenterCross(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_buy_signal_triggers(self):
        df = SF.build_dataframe(values={'MACD':[-1,-.8,-.5,-.003,.01]})
        signal = MACDCenterCross(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)
        assert(signal.description is not None)

    def test_sell_signal_triggers(self):
        df = SF.build_dataframe(values={'MACD':[1,.8,.5,.003,-.01]})
        signal = MACDCenterCross(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)
        assert(signal.description is not None)

    def test_no_signal_triggers(self):
        df = SF.build_dataframe(values={'MACD':[1,.8,.5,.003,.01]})
        signal = MACDCenterCross(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == False)
        assert(signal.is_buy_signal == None)
        assert(signal.description is None)

    def test_no_error_thrown_with_little_data(self):
        df = SF.build_dataframe(values={'MACD':[None] * 2})
        signal = MACDCenterCross(df)
        signal.evaluate()
        assert(signal.triggered() == False)
        assert(signal.is_buy_signal == None)
        assert(signal.description is None)

class TestMACDSignalCross(unittest.TestCase):
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_buy_signal_triggers(self):
        df = SF.build_dataframe(values={'MACD':[-1,-.8,-.5,-.003,.01],
                                        'MACD-Signal':[.5,.4,.3,.2,0]})
        signal = MACDSignalCross(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)
        assert(signal.description is not None)

    def test_sell_signal_triggers(self):
        df = SF.build_dataframe(values={'MACD':[1,.8,.5,.003,-.01],
                                        'MACD-Signal':[-.5,-.4,-.3,-.2,0]})
        signal = MACDSignalCross(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)
        assert(signal.description is not None)

    def test_no_signal_triggers(self):
        df = SF.build_dataframe(values={'MACD':[1,.8,.5,.003,.001],
                                        'MACD-Signal':[.5,.4,.3,.002,0]})
        signal = MACDSignalCross(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == False)
        assert(signal.is_buy_signal == None)
        assert(signal.description is None)

class TestRSI(unittest.TestCase):

    def setUp(self):
        db.create_all()
        self.df = SF.build_dataframe(values={'Adj Close':[45.15, 46.26, 46.5,
                                                          46.23, 46.08, 46.03,
                                                          46.83, 47.69, 47.54,
                                                          49.25, 49.23, 48.2,
                                                          47.57, 47.61, 48.08,
                                                          47.21, 46.76]})

    def tearDown(self):
        db.drop_all()
        pass

    def test_RSI_correctness(self):
        self.df = RSI(self.df).calculate()
        assert('RSI' in self.df.columns)
        assert(isnull(self.df['RSI'][13]))
        # crunched the numbers in Excel.
        self.assertAlmostEqual(self.df['RSI'][14], 69.46, 2)
        self.assertAlmostEqual(self.df['RSI'][16], 58.18, 2)

class TestRSISignal(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()
        db.session.add(self.stock)

    def tearDown(self):
        db.drop_all()

    def test_RSI_triggers_buy_signal(self):
        df = SF.build_dataframe(values={'RSI':[30]*10+[31]})
        print df
        signal = RSISignal(df)
        signal.evaluate()
        print signal
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)

    def test_RSI_triggers_sell_signal(self):
        df = SF.build_dataframe(values={'RSI':[71]*10+[69]})
        signal = RSISignal(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)

    def test_RSI_signal_does_not_fire(self):
        df = DataFrame({'RSI': [50]})
        signal = RSISignal(df)
        signal.evaluate()
        assert(signal.is_buy_signal == None)
