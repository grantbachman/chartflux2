import unittest
from app.models import Stock, StockPoint, Signal, RSI, RSISignal, MACD
from app.models import MACDSignalCross, MACDCenterCross
import StockFactory as SF
from app import db

class TestSMA50SignalInteraction(unittest.TestCase):
    ''' This class tests that SMA50Price signals are appropriately added
    (or not added) to a Stock's signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_triggered_signal_is_appended_to_stock(self):
        ''' There needs to be a non-NaN SMA value for at least 10 days
        for the signal to trigger.'''
        df = SF.build_dataframe(values={'Adj Close':[1]*50+[50]*10+[1]})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(any(x.signal_type == 'SMA50-Price-Cross' for x in self.stock.signals))
    
    def test_untriggered_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[1]*50+[50]*10})
        self.stock._save_dataframe(df)
        print self.stock.signals
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(all(x.signal_type != 'SMA50-Price-Cross' for x in self.stock.signals))


class TestSMA200SignalInteraction(unittest.TestCase):
    ''' This class tests that SMA200Price signals are appropriately added
    (or not added) to a Stock's signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_triggered_signal_is_appended_to_stock(self):
        ''' There needs to be a non-NaN SMA value for at least 50 days
        for the signal to trigger.'''
        df = SF.build_dataframe(values={'Adj Close':[1]*200+[50]*50+[1]})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(any(x.signal_type == 'SMA200-Price-Cross' for x in self.stock.signals))
    
    def test_untriggered_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[1]*200+[50]*50})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(all(x.signal_type != 'SMA200-Price-Cross' for x in self.stock.signals))

class TestRSISignalInteraction(unittest.TestCase):
    ''' This class tests that RSI signals are appropriately added
    (or not added) to a Stock's signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_triggered_signal_is_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[x+1 for x in range(24)]+[10]})
        self.stock._save_dataframe(df)
        print self.stock.signals
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(any(x.signal_type == 'RSI' for x in self.stock.signals))
    
    def test_untriggered_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[x+1 for x in range(25)]})
        self.stock._save_dataframe(df)
        print self.stock.signals
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(all(x.signal_type != 'RSI' for x in self.stock.signals))

class TestMACDCenterCrossInteraction(unittest.TestCase):
    ''' This class tests that MACD Center Cross signals
    are appropriately added (or not added) to a Stock's
    signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_triggered_signal_is_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[10,1,2,3,4,5,6]}) 
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        print self.stock.signals
        assert(any(x.signal_type == 'MACD-Center-Line-Crossover' for x in self.stock.signals))
    
    def test_untriggered_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[10,1,2,3,4,5]}) 
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(all(x.signal_type != 'MACD-Center-Line-Crossover' for x in self.stock.signals))

class TestMACDSignalCrossInteraction(unittest.TestCase):
    ''' This class tests that MACD Signal Cross signals
    are appropriately added (or not added) to a Stock's
    signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_triggered_signal_is_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[5,4,3,2,1,2,4]})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(any(x.signal_type == 'MACD-Signal-Line-Crossover' for x in self.stock.signals))
    
    def test_untriggered_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[5,4,3,2,1,2,3]}) 
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(all(x.signal_type != 'MACD-Signal-Line-Crossover' for x in self.stock.signals))
