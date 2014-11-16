import unittest
from app.models import Stock, StockPoint, Signal, RSI, RSISignal, MACD
from app.models import MACDSignalCross, MACDCenterCross
import StockFactory as SF
from app import db

class TestRSISignalInteraction(unittest.TestCase):
    ''' This class tests that RSI signals are appropriately added
    (or not added) to a Stock's signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_trigged_signal_is_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close': [45.15, 46.26, 46.5, 46.23, 46.08, 46.03, 46.83, 47.69, 47.54, 49.25, 49.23, 48.2, 47.57, 47.61, 48.08, 47.21, 50.76]})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(any(x.signal_type == 'RSI' for x in self.stock.signals))
    
    def test_untrigged_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close': [45.15, 46.26, 46.5, 46.23, 46.08, 46.03, 46.83, 47.69, 47.54, 49.25, 49.23, 48.2, 47.57, 47.61, 48.08, 47.21, 47.76]})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(len(self.stock.signals) == 0)

class TestMACDCenterCrossInteraction(unittest.TestCase):
    ''' This class tests that MACD Center Cross signals
    are appropriately added (or not added) to a Stock's
    signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_trigged_signal_is_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[10,1,2,3,4,5,6]}) 
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        print self.stock.signals
        assert(any(x.signal_type == 'MACD-Center-Line-Crossover' for x in self.stock.signals))
    
    def test_untrigged_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[10,1,2,3,4,5]}) 
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(len(self.stock.signals) == 0)

class TestMACDSignalCrossInteraction(unittest.TestCase):
    ''' This class tests that MACD Signal Cross signals
    are appropriately added (or not added) to a Stock's
    signal list. '''

    def setUp(self):
        db.create_all()
        self.stock = SF.build_stock()

    def tearDown(self):
        db.drop_all()

    def test_trigged_signal_is_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[5,4,3,2,1,2,4]})
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(any(x.signal_type == 'MACD-Signal-Line-Crossover' for x in self.stock.signals))
    
    def test_untrigged_signal_is_not_appended_to_stock(self):
        df = SF.build_dataframe(values={'Adj Close':[5,4,3,2,1,2,3]}) 
        self.stock._save_dataframe(df)
        assert(len(self.stock.signals) == 0)
        self.stock.calculate_indicators()
        assert(len(self.stock.signals) == 0)
