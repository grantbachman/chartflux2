from pandas.io.data import DataReader
import pandas as pd
import datetime as dt
from app import db
import logging
from sqlalchemy import func
from sqlalchemy.sql.expression import asc, desc
from sqlalchemy.ext.orderinglist import ordering_list

def today():
    ''' datetime is implemented in C, which you can't patch.
        This is the easiest way (for me) to keep everything tested.
        Just replacing every call to dt.date.today with today() '''
    return dt.date.today()

class Stock(db.Model):
    ''' Stock class. It's the base class for all attributes about a company '''
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(8))
    name = db.Column(db.String(100))
    market = db.Column(db.String(10))    # could make this a category
    stockpoints = db.relationship('StockPoint', order_by=asc('stock_point.date'))
    signals = db.relationship('Signal', order_by=desc('signal.expiration_date'))

    LOOKBACK_DAYS = 2000

    def __init__(self, symbol=symbol, name=name, market=market):
        self.symbol = symbol.upper()
        self.name = name
        self.market = market

    def __repr__(self):
        return "<Stock(id='%s', symbol='%s', name='%s', market='%s')>" % \
            (self.id, self.symbol, self.name, self.market)

    @staticmethod
    def find_52_week_highs():
        buy_list = db.session.query(Stock, Signal)


    @staticmethod
    def find_buy_stocks():
        ''' Returns a list of (Stock.id, #signals) tuples '''
        buy_list = db.session.query(Stock, func.count(Signal.stock_id))\
            .filter(Stock.id == Signal.stock_id)\
            .filter(Signal.is_buy_signal == True)\
            .filter(Signal.expiration_date >= dt.date.today())\
            .group_by(Stock.id).having(func.count(Signal.stock_id) > 1).all()
        return buy_list

    @staticmethod
    def find_sell_stocks():
        ''' Returns a list of (Stock.id, #signals) tuples '''
        sell_list = db.session.query(Stock, func.count(Signal.stock_id))\
            .filter(Stock.id == Signal.stock_id)\
            .filter(Signal.is_buy_signal == False)\
            .filter(Signal.expiration_date >= dt.date.today())\
            .group_by(Stock.id).having(func.count(Signal.stock_id) > 1).all()
        return sell_list

    def calculate_adjusted_ohlc(self, df):
        df['Adj High'] = df['High'] * (df['Adj Close']/df['Close'])
        df['Adj Low'] = df['Low'] * (df['Adj Close']/df['Close'])
        df['Adj Open'] = df['Open'] * (df['Adj Close']/df['Close'])
        return df

    def calculate_indicators(self):
        df = self.load_dataframe_from_db()
        df = self.calculate_adjusted_ohlc(df)
        df = FiftyTwoWeek(df, 'High').calculate()
        df = FiftyTwoWeek(df, 'Low').calculate()
        df = RSI(df).calculate()
        df = MACD(df).calculate()
        df = SMA(df, 50).calculate()
        df = SMA(df, 200).calculate() 
        rsi_signal = RSISignal(df)
        rsi_signal.evaluate()
        if rsi_signal.triggered() == True:
            self.signals.append(rsi_signal)
        macd_center_cross_signal = MACDCenterCross(df)
        macd_center_cross_signal.evaluate()
        if macd_center_cross_signal.triggered() == True:
            self.signals.append(macd_center_cross_signal)
        macd_signal_cross_signal= MACDSignalCross(df)
        macd_signal_cross_signal.evaluate()
        if macd_signal_cross_signal.triggered() == True:
            self.signals.append(macd_signal_cross_signal)
        sma50_price_cross_signal = SMA50PriceCross(df)
        sma50_price_cross_signal.evaluate()
        if sma50_price_cross_signal.triggered() == True:
            self.signals.append(sma50_price_cross_signal)
        sma200_price_cross_signal = SMA200PriceCross(df)
        sma200_price_cross_signal.evaluate()
        if sma200_price_cross_signal.triggered() == True:
            self.signals.append(sma200_price_cross_signal)
        fifty_two_high_signal = FiftyTwoWeekSignal(df)
        fifty_two_high_signal.evaluate()
        if fifty_two_high_signal.triggered() == True:
            self.signals.append(fifty_two_high_signal)
        fifty_two_low_signal = FiftyTwoWeekSignal(df)
        fifty_two_low_signal.evaluate()
        if fifty_two_low_signal.triggered() == True:
            self.signals.append(fifty_two_high_signal)
        self.update_dataframe(df) # saves new df columns and any new signals

    def update_dataframe(self,df):
        ''' Loops through the rows and saving off the values. This
        method is sort of like _save_dataframe, except it doesn't
        create anything new, just updates. '''
        df = df.reset_index()
        for row_index, row in df.iterrows():
            self.stockpoints[row_index].rsi = df.loc[row_index]['RSI']
            self.stockpoints[row_index].macd = df.loc[row_index]['MACD']
            self.stockpoints[row_index].macd_signal = df.loc[row_index]['MACD-Signal']
            self.stockpoints[row_index].sma_50 = df.loc[row_index]['SMA-50']
            self.stockpoints[row_index].sma_200 = df.loc[row_index]['SMA-200']
            self.stockpoints[row_index].adj_open = df.loc[row_index]['Adj Open']
            self.stockpoints[row_index].adj_high = df.loc[row_index]['Adj High']
            self.stockpoints[row_index].adj_low = df.loc[row_index]['Adj Low']
            self.stockpoints[row_index].high_52_weeks = df.loc[row_index]['52-Week-High']
            self.stockpoints[row_index].low_52_weeks = df.loc[row_index]['52-Week-Low']
        try:
            db.session.commit() # commits new signals
        except:
            db.session.rollback()

    def get_dataframe(self):
        if not self.stockpoints:
            self.fetch_and_save_all_ohlc()
        else:
            self.fetch_and_save_missing_ohlc()
        return self.load_dataframe_from_db()

    def load_dataframe_from_db(self):
        df = pd.DataFrame(db.engine.execute("""SELECT date,open,adj_open,high,
                                            adj_high,low,adj_low,close,
                                            adj_close,volume,rsi,macd,
                                            macd_signal,high_52_weeks,
                                            low_52_weeks,sma_50,sma_200
                                            FROM stock_point
                                            WHERE stock_id = %s
                                            ORDER BY date ASC"""\
                                            % self.id).fetchall())

        if len(df) > 0: # can't add columns when the DF is empty or you get
                        # ValueError: Length mismatch
            df.columns = ['Date','Open','Adj Open','High','Adj High','Low', \
                          'Adj Low','Close','Adj Close','Volume','RSI','MACD',\
                          'MACD-Signal','52-Week-High','52-Week-Low',
                          'SMA-50','SMA-200']
            df.set_index(pd.DatetimeIndex(df['Date']), inplace=True)
            df.drop('Date', axis=1, inplace=True)
        return df

    def _save_dataframe(self, df): 
        ''' Given a dataframe, saves all the rows as new StockPoints.
        Only the OHLCV data gets saved during this process.
        This method gets called during nightly processing.
        '''

        if Stock.query.filter(Stock.symbol==self.symbol,
                              Stock.market==self.market).count() == 0:
            db.session.add(self)

        for index, row in df.iterrows():
            try:
                # Attempt to call float() on each value in the row.
                # If that call errs for whatever reason, then don't save the row.
                [float(val) for ix,val in enumerate(row)]
            except:
                logging.warning('Error with %s. Tried to save row %s with values %s, but the row has something invalid.' % (self, index, row))
            else:
                newPoint = StockPoint(date=index.date(), open=row['Open'],
                                      high=row['High'], low=row['Low'],
                                      close=row['Close'], adj_close=row['Adj Close'],
                                      volume=row['Volume'])
                self.stockpoints.append(newPoint)
        try:
            db.session.commit()
        except Exception as e:
            logging.warning('%s: Error with %s. Tried to save dataframe, but the transaction was rolled back.' % (e, self))
            db.session.rollback()

    def _should_fetch(self):
        ''' Checks if there are any weekdays between the last point
        we have saved and today. It's a better method of determination
        than just checking if it's currently the weekend or not as it
        handles long periods of not grabbing data.
        '''
        last_point_date = self.stockpoints[-1].date
        difference = (today() - last_point_date).days
        return any([(today() - dt.timedelta(days=x)).weekday() not
                    in (5,6) for x in range(1,difference)])

    def fetch_and_save_missing_ohlc(self):
        ''' Grabs the last point of the Stock's data to figure out for what 
        dates it needs to query. Then saves off the data in the Stock's table.
        '''
        if not self._should_fetch():
            return
        next_point_date = self.stockpoints[-1].date + dt.timedelta(days=1)
        yesterday = today() - dt.timedelta(days=1) 
        df = self.fetch_ohlc_from_yahoo(next_point_date, yesterday)
        if df.shape[0] > 0: # save if there's at least one row
            self._save_dataframe(df)               
    
    def fetch_and_save_all_ohlc(self):
        ''' Fetches the model's maximum number of data points '''
        end_date = today()
        start_date  = end_date - dt.timedelta(days = Stock.LOOKBACK_DAYS)
        df = self.fetch_ohlc_from_yahoo(start_date, end_date)
        if df is not None:
            self._save_dataframe(df)

    def fetch_ohlc_from_yahoo(self,start_date,end_date):
        ''' Fetches data for specified dates'''
        try:
            df = DataReader(self.symbol, "yahoo", start_date, end_date)
            ''' When using Google as a data source, the index name gets returned
                prepended with a byte-order mark '\xef\xbb\xbfDate', so rename it '''
        except IOError:   # Raised when symbol isn't found
            return None
        else:
            ''' When using Google as a data source, the index name gets returned
                prepended with a byte-order mark '\xef\xbb\xbfDate', so rename it '''
            df.index.name = 'Date'
            return df

class StockPoint(db.Model):
    ''' This class holds the relevant data for any given day. '''

    __tablename__ = 'stock_point'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
    high = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
    low =  db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
    close = db.Column(db.Float(precision=2 ,asdecimal=True), nullable=False)
    adj_open = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)
    adj_high = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)
    adj_low =  db.Column(db.Float(precision=2, asdecimal=True), nullable=True)
    adj_close = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    avg_volume_3_months = db.Column(db.Integer, nullable=True)  
    sma_50 = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)
    sma_200 = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)

    
    # 52 week high/low is the intra-day high/low, not the closing prices
    high_52_weeks = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)
    low_52_weeks = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)
    
    rsi = db.Column(db.Float(precision=2, asdecimal=True), nullable=True)

    # stores the current MACD values (MACD and the MACD-Signal line)
    macd = db.Column(db.Float(precision=2, asdecimal=True))
    macd_signal = db.Column(db.Float(precision=2, asdecimal=True))
        
    def __init__(self, date, open, high, low, close, adj_close, volume,
                 rsi=None, macd=None, macd_signal=None, adj_open=None,
                 adj_high=None, adj_low=None, high_52_weeks=None,
                 low_52_weeks=None):
        ''' Required: date, open, high, low, close, adj_Close, volume
            Optional: rsi, macd, macd_signal
        '''
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.adj_close = adj_close
        self.volume = volume
        self.rsi = rsi
        self.macd = macd
        self.macd_signal = macd_signal
        self.adj_open = adj_open
        self.adj_high = adj_high
        self.adj_low = adj_low
        self.high_52_weeks = high_52_weeks
        self.low_52_weeks = low_52_weeks

    @staticmethod
    def last_known_date():
        return StockPoint.query.order_by(StockPoint.date.desc()).first().date

    def __repr__(self):
        return "<StockPoint(id='%s', stock_id='%s', date='%s', open='%s', " \
            "high='%s', low='%s', close='%s', adj_close='%s',volume='%s', " \
            "rsi='%s')>" % \
            (self.id, self.stock_id, self.date, self.open, self.high, \
             self.low, self.close, self.adj_close, self.volume, self.rsi)


class Signal(db.Model):
    ''' This is a base class for all of the different types of signals a stock can have '''
    
    __tablename__ = 'signal'
    
    WEIGHT = 0.5
    EXPIRATION_DAYS = 5
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    expiration_date = db.Column(db.Date, nullable=False)
    created_date = db.Column(db.Date, nullable=False, default=dt.date.today())

    # A number between 0 and 1
    weight = db.Column(db.Float(asdecimal=True), nullable=False)

    # this variable only gets set if the signal fires, otherwise it's None
    is_buy_signal = db.Column(db.Boolean, nullable=False)

    # stores the identity of the class that's stored in a given row
    signal_type = db.Column(db.String(64), nullable=False)

    # free text that further describes the signal. 
    description = db.Column(db.String(1024), nullable=True)

    ''' Enables this table to store multiple classes of information (signals)
    with the type of class being stored in the "signal_type" column '''
    __mapper_args__ = { 'polymorphic_on' : 'signal_type', 'polymorphic_identity' : 'Generic' }

    def __init__(self):
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=RSISignal.EXPIRATION_DAYS)
        self.weight = RSISignal.WEIGHT

    def __repr__(self):
        return "<Signal(id='%s', stock_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', created_date='%s', expiration_date='%s', " \
            "weight='%s', description='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, \
             self.signal_type, self.created_date, self.expiration_date, \
             self.weight, self.description)

    def triggered(self):
        ''' We only store an is_buy_signal column as also including an
        is_sell_signal would be redundant.
        '''
        return self.is_buy_signal is not None

    def evaluate(self):
        ''' This function evaluates a stock for the given signal, and
        if it qualifies, sets the "is_buy_signal" and "description" 
        attributes. Each signal has an evaluate method
        '''
        pass

class FiftyTwoWeek(object):
    ''' Class to calculate the 52 Week High/Low prices '''
     
    def __init__(self, df, col):
        ''' col = Column to calculate (High or Low) '''
        self.df = df
        self.col = col

    def calculate(self):
        col = '52-Week-%s' % self.col
        if self.col == 'High':
            self.df[col] = pd.rolling_max(self.df['Adj High'], 365)
        elif self.col == 'Low':
            self.df[col] = pd.rolling_min(self.df['Adj Low'], 365)
        return self.df

class FiftyTwoWeekSignal(Signal):

    __mapper_args__ = {'polymorphic_identity' : 'Fifty-Two-Week'}

    EXPIRATION_DAYS = 1
    WEIGHT = 0.5

    def __init__(self, df):
        self.df = df
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=self.EXPIRATION_DAYS)
        self.weight = self.WEIGHT
    
    def __repr__(self):
        return "<FiftyTwoWeekSignal(id='%s', stock_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', created_date='%s', expiration_date='%s', " \
            "weight='%s', description='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, \
             self.signal_type, self.created_date, self.expiration_date, \
             self.weight, self.description)

    def evaluate(self):
        if self.df['52-Week-High'][-2] < self.df['52-Week-High'][-1]:
            self.is_buy_signal = True
            self.description = "Price just broke through 52 Week High."
        elif self.df['52-Week-Low'][-2] > self.df['52-Week-Low'][-1]:
            self.is_buy_signal = False
            self.description = "Price just fell through 52 Week Low."

class SMA(object):
    ''' Class to calculate the simple moving average '''

    def __init__(self, df, span):
        self.df = df
        self.span = span

    def calculate(self):
        col = 'SMA-%s' % self.span
        self.df[col] = pd.rolling_mean(self.df['Adj Close'], self.span)
        return self.df

class SMA50PriceCross(Signal):

    __mapper_args__ = {'polymorphic_identity' : 'SMA50-Price-Cross'}

    BEFORE = 10
    AFTER = 1
    DATA_REQ = BEFORE + AFTER  # Data Requirements 
    EXPIRATION_DAYS = 5
    WEIGHT = 0.5

    def __init__(self, df):
        self.df = df
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=self.EXPIRATION_DAYS)
        self.weight = self.WEIGHT

    def __repr__(self):
        return "<SMA50PriceCross(id='%s', stock_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', created_date='%s', expiration_date='%s', " \
            "weight='%s', description='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, \
             self.signal_type, self.created_date, self.expiration_date, \
             self.weight, self.description)
    
    def evaluate(self):
        if (self.df['SMA-50'][-self.DATA_REQ:-self.AFTER] >= \
                self.df['Adj Close'][-self.DATA_REQ:-self.AFTER]).all() and \
        (self.df['SMA-50'][-self.AFTER:] < self.df['Adj Close'][-self.AFTER:]).all():
            self.is_buy_signal = True
            self.description = "Price just turned above the 50 Day Simple Moving Average."
        elif (self.df['SMA-50'][-self.DATA_REQ:-self.AFTER] <= \
                self.df['Adj Close'][-self.DATA_REQ:-self.AFTER]).all() and \
        (self.df['SMA-50'][-self.AFTER:] > self.df['Adj Close'][-self.AFTER:]).all():
            self.is_buy_signal = False
            self.description = "Price just dropped below the 50 Day Simple Moving Average."

class SMA200PriceCross(Signal):

    __mapper_args__ = {'polymorphic_identity' : 'SMA200-Price-Cross'}

    BEFORE = 50 
    AFTER = 1
    DATA_REQ = BEFORE + AFTER  # Data Requirements 
    EXPIRATION_DAYS = 5
    WEIGHT = 1

    def __init__(self, df):
        self.df = df
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=self.EXPIRATION_DAYS)
        self.weight = self.WEIGHT

    def __repr__(self):
        return "<SMA200PriceCross(id='%s', stock_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', created_date='%s', expiration_date='%s', " \
            "weight='%s', description='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, \
             self.signal_type, self.created_date, self.expiration_date, \
             self.weight, self.description)
    
    def evaluate(self):
        if (self.df['SMA-200'][-self.DATA_REQ:-self.AFTER] >= \
                self.df['Adj Close'][-self.DATA_REQ:-self.AFTER]).all() and \
        (self.df['SMA-200'][-self.AFTER:] < self.df['Adj Close'][-self.AFTER:]).all():
            self.is_buy_signal = True
            self.description = "Price just turned above the 200 Day Simple Moving Average."
        elif (self.df['SMA-200'][-self.DATA_REQ:-self.AFTER] <= \
                self.df['Adj Close'][-self.DATA_REQ:-self.AFTER]).all() and \
        (self.df['SMA-200'][-self.AFTER:] > self.df['Adj Close'][-self.AFTER:]).all():
            self.is_buy_signal = False
            self.description = "Price just dropped below the 200 Day Simple Moving Average."

class RSI(object):

    LOOKBACK = 14  

    def __init__(self, df):
        self.df = df

    def calculate(self):
        rsi_df = pd.DataFrame( {'Change' : self.df['Adj Close'].diff(),
                               'Gain' : 0,
                               'Loss' : 0,
                               'Avg Gain': 0,
                               'Avg Loss': 0,
                               })
        rsi_df.index.name='Date'
        rsi_df.reset_index(inplace=True)
        ''' Calculate the first Average Gain and Average Loss, which is
        the simple mean of Gains and Losses for the first 14 datapoints
        with a Change (so, rows 1 thru 15). The Average Loss is
        expressed as a positive value
        '''
        rsi_df['Gain'] = rsi_df['Change'][rsi_df['Change'] > 0]
        rsi_df['Loss'] = rsi_df['Change'][rsi_df['Change'] < 0] * -1
        rsi_df.fillna(value=0, inplace=True)
        rsi_df.loc[RSI.LOOKBACK,'Avg Gain'] = \
            rsi_df['Gain'][1:RSI.LOOKBACK+1].mean()
        rsi_df.loc[RSI.LOOKBACK,'Avg Loss'] = \
            rsi_df['Loss'][1:RSI.LOOKBACK+1].mean()

        ''' The rest of the Avg Gain/Avg Loss points use the following
        formula:
        Average Gain = (previous_Avg_Gain * 13 + current_Gain) / 14 
        Average Loss = (previous_Avg_Loss * 13 + current_Loss) /14

        Note: I spent a good 2 hours trying to figure out a way to do
        this by pure dataframe manipulation, to no avail. Eventually,
        you just have to move on.
        '''
        for index, row in rsi_df.iterrows():
            ''' Using .ix[index] accesses the actual dataframe, using 
            [index] just accesses a copy 
            '''
            if index > RSI.LOOKBACK:  
                rsi_df.loc[index,'Avg Gain'] = (rsi_df['Avg Gain'][index-1] * (RSI.LOOKBACK - 1) + rsi_df['Gain'][index]) / RSI.LOOKBACK
                rsi_df.loc[index,'Avg Loss'] = (rsi_df['Avg Loss'][index-1] * (RSI.LOOKBACK - 1) + rsi_df['Loss'][index]) / RSI.LOOKBACK 
        rsi_df['RS'] = rsi_df['Avg Gain'] / rsi_df['Avg Loss']
        rsi_df.set_index(keys='Date', drop=True, inplace=True)
        self.df['RSI'] = 100 - (100 / (1 + rsi_df['RS']))
        return self.df

class RSISignal(Signal):

    __mapper_args__ = {'polymorphic_identity' : 'RSI'}

    OVERBOUGHT = 70
    OVERSOLD = 30
    WEIGHT = 0.5
    # Min number of days MACD must be on one side before crossing
    BEFORE = 10 
    # After crossing, min number of days it must stay on that side before the
    # signal fires 
    AFTER = 1
    DATA_REQ = BEFORE + AFTER  # Data Requirements 
    EXPIRATION_DAYS = 5  # Number of days until expiration

    def __init__(self, df):
        self.df = df
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=RSISignal.EXPIRATION_DAYS)
        self.weight = RSISignal.WEIGHT

    def __repr__(self):
        return "<RSISignal(id='%s', stock_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', created_date='%s', expiration_date='%s', " \
            "weight='%s', description='%s', RSISignal.OVERBOUGHT='%s'," \
            " RSISignal.OVERSOLD='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, \
             self.signal_type, self.created_date, self.expiration_date, \
             self.weight, self.description, RSISignal.OVERBOUGHT, \
             RSISignal.OVERSOLD)


    def evaluate(self):
        """ RSI can remain overbought or oversold for long periods of
        time. Counter-intuitively, when the RSI falls from
        overbought territory, it signals a swing towards negative
        momentum (i.e. sell signal), and vice versa.
        """
        last = self.df['RSI'][len(self.df)-RSISignal.DATA_REQ:]
        if (last.iloc[:RSISignal.BEFORE] >= RSISignal.OVERBOUGHT).all() and \
        (last.iloc[RSISignal.BEFORE:] < RSISignal.OVERBOUGHT).all():
            self.is_buy_signal = False
            self.description = "RSI (%s) is returning from overbought" \
              " territory, signaling a negative change in momentum." \
              % format(last.iloc[-1], '.2f')
        elif (last.iloc[:RSISignal.BEFORE] <= RSISignal.OVERSOLD).all() and \
        (last.iloc[RSISignal.BEFORE:] > RSISignal.OVERSOLD).all():
            self.is_buy_signal = True
            self.description = "RSI (%s) is returning from oversold" \
              " territory, signaling a positive change in momentum." \
              % format(last.iloc[-1], '.2f')
        else:
            pass

class MACD(object):

    SLOW_SPAN = 26
    FAST_SPAN = 12
    SMOOTHING_SPAN = 9

    def __init__(self, df):
        self.df = df

    def calculate(self):
        tempDF= pd.DataFrame({ 'Adj Close' : self.df['Adj Close']})
        tempDF['FAST'] = pd.ewma(tempDF['Adj Close'],
                                  span=MACD.FAST_SPAN)
        tempDF['SLOW'] = pd.ewma(tempDF['Adj Close'],
                                  span=MACD.SLOW_SPAN)
        tempDF['MACD'] = tempDF['FAST'] - tempDF['SLOW']
        self.df['MACD-Signal'] = pd.ewma(tempDF['MACD'], span=MACD.SMOOTHING_SPAN)
        self.df['MACD'] = tempDF['MACD']
        return self.df

class MACDSignalCross(Signal):
    
    __mapper_args__ = {'polymorphic_identity': 'MACD-Signal-Line-Crossover'}

    # Min number of days MACD must be on one side before crossing
    BEFORE = 4 
    # After crossing, min number of days it must stay on that side before the
    # signal fires 
    AFTER = 1
    DATA_REQ = BEFORE + AFTER  # Data Requirements 
    WEIGHT = 0.5
    EXPIRATION_DAYS = 3  # Number of days until expiration

    def __init__(self, df):
        self.df = df
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=MACDSignalCross.EXPIRATION_DAYS)
        self.weight = MACDSignalCross.WEIGHT

    def __repr__(self):
        return "<MACDSignalCross(id='%s', stock_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', created_date='%s', expiration_date='%s', " \
            "weight='%s', description='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, \
             self.signal_type, self.created_date, self.expiration_date, \
             self.weight, self.description)

    def may_evaluate(self):
        ''' Returns whether there is enough data to do an analysis '''
        return len(self.df['MACD']) >= MACDCenterCross.DATA_REQ

    def evaluate(self):
        ''' If the MACD crosses the MACD-Signal line in the last two 
        datapoints, then it qualifies for the signal.
        
        Bullish: MACD turns up and crosses above the Signal Line
        Bearish: MACD turns down and crosses below the Signal Line
        '''

        # Check if we can safely evalute without getting KeyErrors
        if not self.may_evaluate():
            return

        # check to ensure only the most recent day (of the past 5) has
        # broken the threshold to help prevent thrashing.
        last = self.df[['MACD','MACD-Signal']][len(self.df)-MACDSignalCross.DATA_REQ:]

        if (last['MACD'][:MACDSignalCross.BEFORE] <= \
            last['MACD-Signal'][:MACDSignalCross.BEFORE]).all() and \
           (last['MACD'][MACDSignalCross.BEFORE:] > \
            last['MACD-Signal'][MACDSignalCross.BEFORE:]).all():
            self.is_buy_signal = True
            self.description = "MACD (%s) just turned above the Signal Line" \
                " (%s)" % (format(last['MACD'].iloc[-1],'.2f'), format(last['MACD-Signal'].iloc[-1],'.2f'))
        elif (last['MACD'][:MACDSignalCross.BEFORE] >= \
            last['MACD-Signal'][:MACDSignalCross.BEFORE]).all() and \
           (last['MACD'][MACDSignalCross.BEFORE:] < \
            last['MACD-Signal'][MACDSignalCross.BEFORE:]).all():
            self.is_buy_signal = False 
            self.description = "MACD (%s) just dropped below the Signal Line" \
                " (%s)" % (format(last['MACD'].iloc[-1],'.2f'), format(last['MACD-Signal'].iloc[-1],'.2f'))
        else:
            pass

class MACDCenterCross(Signal):
    
    __mapper_args__ = {'polymorphic_identity': 'MACD-Center-Line-Crossover'}

    # Min number of days MACD must be on one side before crossing
    BEFORE = 4 
    # After crossing, min number of days it must stay on that side before the
    # signal fires 
    AFTER = 1
    DATA_REQ = BEFORE + AFTER  # Data Requirements 
    WEIGHT = 0.5
    EXPIRATION_DAYS = 3  # Number of days until expiration

    def __init__(self, df):
        self.df = df
        self.expiration_date = dt.date.today() + \
                               dt.timedelta(days=MACDCenterCross.EXPIRATION_DAYS)
        self.weight = MACDCenterCross.WEIGHT

    def __repr__(self):
        return "<MACDCenterCross(id='%s', stock_id='%s', " \
            "is_buy_signal='%s', signal_type='%s', created_date='%s', " \
            "expiration_date='%s', weight='%s', description='%s')>" % \
            (self.id, self.stock_id, self.is_buy_signal, self.signal_type, \
             self.created_date, self.expiration_date, self.weight, \
             self.description)

    def may_evaluate(self):
        ''' Returns whether there is enough data to do an analysis '''
        return len(self.df['MACD']) >= MACDCenterCross.DATA_REQ

    
    def evaluate(self):
        ''' If the MACD goes from positive to negative in the last two
        datapoints or vice versa, then it qualifies for the signal.
        
        Bullish: MACD turns positive
        Bearish: MACD turns negative
        '''
        # Check if we can safely evalute without getting KeyErrors
        if not self.may_evaluate():
            return

        last = self.df['MACD'][len(self.df)-MACDCenterCross.DATA_REQ:]

        if (last[:MACDCenterCross.BEFORE] <= 0).all() and \
                (last[MACDCenterCross.BEFORE:] > 0).all():
            self.expiration_date = dt.date.today() + \
                                   dt.timedelta(days=MACDCenterCross.EXPIRATION_DAYS)
            self.weight = MACDCenterCross.WEIGHT
            self.is_buy_signal = True
            self.description = "MACD (%s) just turned positive." % format(last.iloc[-1],'.2f')
        elif (last[:MACDCenterCross.BEFORE] >= 0).all() and \
                (last[MACDCenterCross.BEFORE:] < 0).all():
            self.expiration_date = dt.date.today() + \
                                   dt.timedelta(days=MACDCenterCross.EXPIRATION_DAYS)
            self.weight = MACDCenterCross.WEIGHT
            self.is_buy_signal = False 
            self.description = "MACD (%s) just turned negative." % format(last.iloc[-1],'.2f')
        else:
            pass
