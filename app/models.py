from pandas.io.data import DataReader
import pandas as pd
import datetime as dt
from app import db
from sqlalchemy.sql.expression import asc

'''
class MACD():
    def calc_macd(self):
        tempDF= pd.DataFrame({ 'Close' : self.df['Close']})
        tempDF['EMA12'] = pd.ewma(tempDF['Close'], span=12)
        tempDF['EMA26'] = pd.ewma(tempDF['Close'], span=26)
        tempDF['MACD'] = tempDF['EMA12'] - tempDF['EMA26']
        self.df['MACD-Signal'] = pd.ewma(tempDF['MACD'], span=9)
        self.df['MACD'] = tempDF['MACD']
'''

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

    LOOKBACK_DAYS = 20000  

    def __init__(self, symbol=symbol, name=name, market=market):
        self.symbol = symbol.upper()
        self.name = name
        self.market = market

    def __repr__(self):
        return "<Stock(id='%s', symbol='%s', name='%s', market='%s')>" % \
            (self.id, self.symbol, self.name, self.market)

    @staticmethod
    def find_buy_stocks():
        return None

    @staticmethod
    def find_sell_stocks():
        return None

    def calculate_indicators(self):
        print("Calculating indicators for %s" % (self.name,))
        df = self.load_dataframe_from_db(reset_index=True)
        rsi = RSISignal(df)
        rsi.calculate()
        rsi.evaluate()
        if rsi.triggered() == True:
            num_points = len(self.stockpoints)
            self.stockpoints[num_points-1].signals.append(rsi)
        self._save_indicators(df) # saves new df columns and any new signals

    def _save_indicators(self,df):
        for row_index, row in df.iterrows():
            if 'RSI' in df:
                self.stockpoints[row_index].rsi = df['RSI'][row_index]
            if 'MACD' in df:
                self.stockpoints[row_index].macd = df.loc[row_index]['MACD']
            if 'MACD-Signal' in df:
                self.stockpoints[row_index].macd_signal = df.loc[row_index]['MACD-Signal']
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

    def load_dataframe_from_db(self, reset_index=False):
        df = pd.DataFrame(columns = ('Date','Open','High','Low','Close', 'Adj Close', 'Volume'))
        df.set_index(keys='Date', drop=True, inplace=True)
        for point in self.stockpoints:
            df.loc[point.date] =[float(point.open),float(point.high),float(point.low),float(point.close),float(point.adj_close),int(point.volume)]
        if reset_index == True:
            df.reset_index(inplace=True)
        return df

    def _save_dataframe(self,df): 
        ''' Saves a dataframe
        If the stock doesn't exist, it creates it.
        '''
        if Stock.query.filter(Stock.symbol==self.symbol,
                              Stock.market==self.market).count() == 0:
            db.session.add(self)
        # get the index in which the date resides so we can skip it
        # when checking the datatypes of the other columns
        for index, row in enumerate(df.columns):
            if row == 'Date': date_col_index = index

        for row_index, row in df.iterrows():
            row['Date']=row['Date'].date()
            try:
                # Attempt to call float() on each value in the row.
                # If that call errs, then don't save the row.
                [float(val) for index,val in enumerate(row) if index != date_col_index]
            except:
                pass
            else:
                newPoint = StockPoint(date=row['Date'], open=row['Open'],
                                      high=row['High'], low=row['Low'],
                                      close=row['Close'], adj_close=row['Adj Close'],
                                      volume=row['Volume'])
                self.stockpoints.append(newPoint)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    def fetch_and_save_missing_ohlc(self):
        '''
        Grabs the last point of the Stock's data to figure out for what 
        dates it needs to query. Then saves off the data in the Stock's table.
        '''
        next_point_date = self.stockpoints[-1].date + dt.timedelta(days=1)
        if next_point_date.weekday() not in (5,6) and \
        next_point_date != today():
            yesterday = today() - dt.timedelta(days=1) 
            df = self.fetch_ohlc_from_yahoo(next_point_date, yesterday)
            if df is not None:
                self._save_dataframe(df)               
    
    def fetch_and_save_all_ohlc(self):
        ''' Fetches the model's maximum number of data points'''
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
            df.index.name = 'Date'
            df.reset_index(inplace=True) # for saving the date
            return df

class StockPoint(db.Model):
    ''' This class holds the relevant data for any given day. '''

    __tablename__ = 'stock_point'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Float(precision=2,asdecimal=True), nullable=False)
    high = db.Column(db.Float(precision=2,asdecimal=True), nullable=False)
    low =  db.Column(db.Float(precision=2,asdecimal=True), nullable=False)
    close = db.Column(db.Float(precision=2,asdecimal=True), nullable=False)
    adj_close = db.Column(db.Float(precision=2,asdecimal=True), nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    rsi = db.Column(db.Float(precision=2,asdecimal=True), nullable=True)

    # stores the current MACD values (MACD and the MACD-Signal line)
    macd = db.Column(db.Float(precision=2,asdecimal=True))
    macd_signal = db.Column(db.Float(precision=2,asdecimal=True))

    # Each StockPoint (each day) can have a variable number of signals that have been triggered
    signals = db.relationship('Signal') 
    # Store the number of signals for easier querying
    num_buy_signals = db.Column(db.Integer, default=0)
    num_sell_signals = db.Column(db.Integer, default=0)
        
    def __init__(self, date=date, open=open, high=high,
                 low=low, close=close, adj_close=adj_close, volume=volume):
        self.date, self.open, self.high, self.low, self.close, self.adj_close, self.volume = date, open, high, low, close, adj_close, volume

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
    
    id = db.Column(db.Integer, primary_key=True)
    stock_point_id = db.Column(db.Integer, db.ForeignKey('stock_point.id'))

    # this variable only gets set if the signal fires, otherwise it's None
    is_buy_signal = db.Column(db.Boolean, nullable=False)

    # stores the identity of the class that's stored in a given row
    signal_type = db.Column(db.String(64), nullable=False)

    # free text that further describes the signal. 
    description = db.Column(db.String(1024), nullable=True)

    ''' Enables this table to store multiple classes of information (signals)
    with the type of class being stored in the "signal_type" column '''
    __mapper_args__ = { 'polymorphic_on' : 'signal_type', 'polymorphic_identity' : 'generic' }

    def __init__(self):
        pass

    def __repr__(self):
        return "<Signal(id='%s', stock_point_id='%s', is_buy_signal='%s', " \
            "signal_type='%s', description='%s')>" % \
            (self.id, self.stock_point_id, self.is_buy_signal, \
             self.signal_type, self.description)

    def triggered(self):
        return self.is_buy_signal is not None


    def calculate(self):
        ''' This function calculates and sets any necessary data that's needed to determine
        whether or not a stock currently qualifies for a given signal '''
        pass
    
    def evaluate(self):
        ''' This function evaluates a stock for the given signal, and if it qualifies, sets
        the "is_buy_signal" and "description" attributes. '''
        pass

class RSISignal(Signal):

    __mapper_args__ = { 'polymorphic_identity' : 'rsi' }

    OVERBOUGHT = 70
    OVERSOLD = 30
    LOOKBACK = 14  # Standard 14 Day look-back period, but can be altered to change signal sensitivity

    def __init__(self, df):
        self.df = df

    def __repr__(self):
        return "<RSISignal(id='%s', stock_point_id='%s', is_buy_signal='%s'," \
            " signal_type='%s', description='%s', RSISignal.OVERBOUGHT='%s'," \
            " RSISignal.OVERSOLD='%s', RSISignal.LOOKBACK='%s')>" % \
            (self.id, self.stock_point_id, self.is_buy_signal, \
             self.signal_type, self.description, RSISignal.OVERBOUGHT, \
             RSISignal.OVERSOLD, RSISignal.LOOKBACK)

    def calculate(self):
        rsi_df = pd.DataFrame( {'Change' : self.df['Adj Close'].diff(),
                               'Gain' : 0,
                               'Loss' : 0,
                               'Avg Gain': 0,
                               'Avg Loss': 0,
                               })
        ''' Calculate the first Average Gain and Average Loss, which is the simple mean of Gains
            and Losses for the first 14 datapoints with a Change (so, rows 1 thru 15). The
            Average Loss is expressed as a positive value '''
        rsi_df['Gain'] = rsi_df['Change'][rsi_df['Change'] > 0]
        rsi_df['Loss'] = rsi_df['Change'][rsi_df['Change'] < 0] * -1
        rsi_df = rsi_df.fillna(value=0)
        rsi_df['Avg Gain'].ix[RSISignal.LOOKBACK] = rsi_df['Gain'][1:RSISignal.LOOKBACK+1].mean()
        rsi_df['Avg Loss'].ix[RSISignal.LOOKBACK] = rsi_df['Loss'][1:RSISignal.LOOKBACK+1].mean()

        ''' The rest of the Avg Gain/Avg Loss points use the following formula:
            Average Gain = (previous_Avg_Gain * 13 + current_Gain) / 14 
            Average Loss = (previous_Avg_Loss * 13 + current_Loss) /14

            Note: I spent a good 2 hours trying to figure out a way to do this by pure dataframe
            manipulation to no avail. Eventually, you just have to move on.''' 
        for index, row in rsi_df.iterrows():
            # using .ix[index] accesses the actual dataframe, using [index] just accesses a copy 
            if index > RSISignal.LOOKBACK:
                rsi_df['Avg Gain'].ix[index] = (rsi_df['Avg Gain'][index-1] * (RSISignal.LOOKBACK - 1) + rsi_df['Gain'][index]) / RSISignal.LOOKBACK
                rsi_df['Avg Loss'].ix[index] = (rsi_df['Avg Loss'][index-1] * (RSISignal.LOOKBACK - 1) + rsi_df['Loss'][index]) / RSISignal.LOOKBACK 
        rsi_df['RS'] = rsi_df['Avg Gain'] / rsi_df['Avg Loss']
        self.df['RSI'] = 100 - (100 / (1 + rsi_df['RS']))

    def evaluate(self):
        ''' Checks the last row of the dataframe, which is the most
        recent date, and checks it against the OVERBOUGHT and OVERSOLD
        thresholds. If that point meets the criteria, the signal's
        is_buy_signal and description are updated.
        '''
        cur_rsi = self.df['RSI'][len(self.df)-1]
        if cur_rsi >= RSISignal.OVERBOUGHT:
            self.is_buy_signal = False
            self.description = "RSI is '%s'" % cur_rsi
        elif cur_rsi <= RSISignal.OVERSOLD:
            self.is_buy_signal = True
            self.description = "RSI is '%s'" % cur_rsi
        else:
            pass

