import unittest
import datetime as dt
from app.models import Stock, StockPoint, Signal, RSISignal
from app import db
from pandas import DataFrame, DatetimeIndex, isnull
from decimal import Decimal

class TestSignal(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        db.session.add(self.stock)
        newPoint = StockPoint(date=dt.date.today(), open=1,
                              high=1, low=1, close=1,
                              adj_close=1, volume=1)
        self.stock.stockpoints.append(newPoint)

    def tearDown(self):
        db.drop_all()

    def test_generic_signal_gets_saved(self):
        assert(len(self.stock.stockpoints[0].signals) == 0)
        signal = Signal()
        signal.is_buy_signal = True
        signal.description = 'Generic Description'
        self.stock.stockpoints[0].signals.append(signal)
        db.session.commit()
        saved_signal = self.stock.stockpoints[0].signals[0]
        print(saved_signal)
        assert(saved_signal is not None)
        assert(isinstance(saved_signal, Signal))
        assert(saved_signal.is_buy_signal == True)
        assert(saved_signal.description == 'Generic Description')
        assert(saved_signal.signal_type == 'generic')

class TestRSISignal(unittest.TestCase):
    
    def setUp(self):
        db.create_all()
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        db.session.add(self.stock)
        newPoint = StockPoint(date=dt.date.today(), open=1,
                              high=1, low=1, close=1,
                              adj_close=1, volume=1)
        self.stock.stockpoints.append(newPoint)

    def tearDown(self):
        db.drop_all()

    def test_RSI_signal_gets_saved(self):
        df = DataFrame()  # to please __init__
        signal = RSISignal(df)
        signal.is_buy_signal = False   # sell signal
        signal.description = 'RSI Description'
        self.stock.stockpoints[0].signals.append(signal)
        db.session.commit()
        saved_signal = self.stock.stockpoints[0].signals[0]
        print(saved_signal)
        assert(saved_signal is not None)
        assert(saved_signal.signal_type == 'rsi') 
        assert(saved_signal.is_buy_signal == False) 
        assert(saved_signal.description == 'RSI Description')

    def test_RSI_signal_correctness(self):
        # 17 days of data
        df = DataFrame({'Adj Close': [45.15, 46.26, 46.5, 46.23, 46.08, 46.03, 46.83, 47.69, 47.54, 49.25, 49.23, 48.2, 47.57, 47.61, 48.08, 47.21, 46.76] })
        signal = RSISignal(df)
        signal.calculate()
        print df['RSI'][16]
        assert('RSI' in df.columns)
        assert(isnull(df['RSI'][13]))
        # crunched the numbers in Excel.
        self.assertAlmostEqual(df['RSI'][14], 69.46, 2)
        self.assertAlmostEqual(df['RSI'][16], 58.18, 2)

    def test_RSI_values_get_saved(self):
        db.session.rollback() # undo setup
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        db.session.add(self.stock)
        days = 17
        dtLst = DatetimeIndex([dt.date.today() - dt.timedelta(days=i) for i in range(days)])
        df = DataFrame({'Adj Close': [45.15, 46.26, 46.5, 46.23, 46.08, 46.03, 46.83, 47.69, 47.54, 49.25, 49.23, 48.2, 47.57, 47.61, 48.08, 47.21, 46.76],
                        'Open': [1] * days,
                        'High': [1] * days,
                        'Low': [1] * days,
                        'Close': [1] * days,
                        'Volume': [1] * days,
                        'Date': list(dtLst)
                        })
        self.stock._save_dataframe(df)
        signal = RSISignal(df)
        signal.calculate()
        self.stock._save_indicators(df)
        assert(self.stock.stockpoints[16].rsi is not None)
        self.assertAlmostEqual(self.stock.stockpoints[16].rsi, Decimal(58.18), 2)

    def test_trigged_signal_is_appended_to_stockpoint(self):
        db.session.rollback() # undo setup
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        db.session.add(self.stock)
        days = 17
        dtLst = DatetimeIndex([dt.date.today() - dt.timedelta(days=i) for i in range(days)])
        # Should have an RSI around ~74 and trigger a buy signal
        df = DataFrame({'Adj Close': [45.15, 46.26, 46.5, 46.23, 46.08, 46.03, 46.83, 47.69, 47.54, 49.25, 49.23, 48.2, 47.57, 47.61, 48.08, 47.21, 50.76],
                        'Open': [1] * days,
                        'High': [1] * days,
                        'Low': [1] * days,
                        'Close': [1] * days,
                        'Volume': [1] * days,
                        'Date': list(dtLst)
                        })
        self.stock._save_dataframe(df)
        num_points = len(self.stock.stockpoints)
        assert(len(self.stock.stockpoints[num_points-1].signals) == 0)
        self.stock.calculate_indicators()
        assert(len(self.stock.stockpoints[num_points-1].signals) == 1)
    
    def test_untrigged_signal_is_not_appended_to_stockpoint(self):
        db.session.rollback() # undo setup
        self.stock = Stock(symbol='tsla',
                           name='Tesla Motors Inc',
                           market='NASDAQ')
        db.session.add(self.stock)
        days = 17
        dtLst = DatetimeIndex([dt.date.today() - dt.timedelta(days=i) for i in range(days)])
        # Should have an RSI around ~40 and not trigger an RSI signal 
        df = DataFrame({'Adj Close': [45.15, 46.26, 46.5, 46.23, 46.08, 46.03, 46.83, 47.69, 47.54, 49.25, 49.23, 48.2, 47.57, 47.61, 48.08, 47.21, 47.76],
                        'Open': [1] * days,
                        'High': [1] * days,
                        'Low': [1] * days,
                        'Close': [1] * days,
                        'Volume': [1] * days,
                        'Date': list(dtLst)
                        })
        self.stock._save_dataframe(df)
        num_points = len(self.stock.stockpoints)
        assert(len(self.stock.stockpoints[num_points-1].signals) == 0)
        self.stock.calculate_indicators()
        assert(len(self.stock.stockpoints[num_points-1].signals) == 0)

    def test_RSI_triggers_buy_signal(self):
        df = DataFrame({'RSI': [30]})
        signal = RSISignal(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == True)

    def test_RSI_triggers_sell_signal(self):
        df = DataFrame({'RSI': [70]})
        signal = RSISignal(df)
        signal.evaluate()
        assert(signal.triggered() == True)
        assert(signal.is_buy_signal == False)

    def test_RSI_signal_does_not_fire(self):
        df = DataFrame({'RSI': [50]})
        signal = RSISignal(df)
        signal.evaluate()
        assert(signal.is_buy_signal == None)
