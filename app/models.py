from pandas.io.data import DataReader
import pandas as pd
import datetime as dt
from app import db
from sqlalchemy.sql.expression import asc

class MACD(object):

    def __init__(self,df):
        self.df = df
        self.calc_macd()

    @staticmethod
    def find_buy_stocks():
        ''' Returns a list of (StockPoint, Stock) tuples '''
        return db.session.query(StockPoint, Stock).filter(StockPoint.stock_id == Stock.id).filter(StockPoint.rsi < RSI.OVERSOLD).filter(StockPoint.date == StockPoint.last_known_date()).all()

    @staticmethod
    def find_sell_stocks():
        ''' Returns a list of (StockPoint, Stock) tuples '''
        return db.session.query(StockPoint, Stock).filter(StockPoint.stock_id == Stock.id).filter(StockPoint.rsi > RSI.OVERBOUGHT).filter(StockPoint.date == StockPoint.last_known_date()).all()
    
    def calc_macd(self):
        tempDF= pd.DataFrame({ 'Close' : self.df['Close']})
        tempDF['EMA12'] = pd.ewma(tempDF['Close'], span=12)
        tempDF['EMA26'] = pd.ewma(tempDF['Close'], span=26)
        tempDF['MACD'] = tempDF['EMA12'] - tempDF['EMA26']
        self.df['MACD-Signal'] = pd.ewma(tempDF['MACD'], span=9)
        self.df['MACD'] = tempDF['MACD']

# datetime is implemented in C, which you can't patch. This is the 
# easiest way (for me) to keep everything tested. Just replacing every call to
# dt.date.today with today()
def today():
    return dt.date.today()

class RSI(object):

    OVERBOUGHT = 70
    OVERSOLD = 30

    def __init__(self,df):
        self.df = df
        self.calc_rsi()

    @staticmethod
    def find_buy_stocks():
        ''' Returns a list of (StockPoint, Stock) tuples '''
        return db.session.query(StockPoint, Stock).filter(StockPoint.stock_id == Stock.id).filter(StockPoint.rsi < RSI.OVERSOLD).filter(StockPoint.date == StockPoint.last_known_date()).all()

    @staticmethod
    def find_sell_stocks():
        ''' Returns a list of (StockPoint, Stock) tuples '''
        return db.session.query(StockPoint, Stock).filter(StockPoint.stock_id == Stock.id).filter(StockPoint.rsi > RSI.OVERBOUGHT).filter(StockPoint.date == StockPoint.last_known_date()).all()

    '''
    def is_buy_signal(self):
        return self.df['RSI'][-1]
    '''

    def calc_rsi(self):
        delta = self.df['Close'].diff()
        rsiDF = pd.DataFrame({"Up" : delta, "Down" : delta})
        rsiDF['Up'] = rsiDF['Up'][rsiDF['Up'] > 0]
        rsiDF['Down'] = rsiDF['Down'][rsiDF['Down'] < 0]
        rsiDF = rsiDF.fillna(value=0)
        rsiDF['UpMean'] = pd.rolling_mean(rsiDF['Up'],14)
        rsiDF['DownMean'] = pd.rolling_mean(rsiDF['Down'],14).abs()
        rsiDF['RS'] = rsiDF['UpMean'] / rsiDF['DownMean']
        rsiDF['RSI'] = 100 - (100/(1+rsiDF['RS']))
        self.df['RSI'] = rsiDF['RSI']

class Stock(db.Model):
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
        return "<Stock(id='%s', symbol='%s', name='%s', market='%s')>" % (
            self.id, self.symbol, self.name, self.market)

    @staticmethod
    def find_buy_stocks():
        rsi_stocks = RSI.find_buy_stocks()
        macd_stocks = MACD.find_buy_stocks()
        return rsi_stocks

    @staticmethod
    def find_sell_stocks():
        rsi_stocks = RSI.find_sell_stocks()
        macd_stocks = MACD.find_sell_stocks()
        return rsi_stocks

    def calculate_indicators(self):
        print("Calculating indicators for %s" % (self.name,))
        df = self.load_dataframe_from_db()
        df = RSI(df).df
        df = MACD(df).df
        df.reset_index(inplace=True)
        self._save_indicators(df)

    def _save_indicators(self,df):
        for row_index, row in df.iterrows():
            if 'RSI' in df:
                self.stockpoints[row_index].rsi = df.loc[row_index]['RSI']
            if 'MACD' in df:
                self.stockpoints[row_index].macd = df.loc[row_index]['MACD']
            if 'MACD-Signal' in df:
                self.stockpoints[row_index].macd_signal = df.loc[row_index]['MACD-Signal']
        try:
            db.session.commit()
        except:
            db.session.rollback()


    def get_dataframe(self):
        if not self.stockpoints:
            self.fetch_and_save_all_ohlc()
        else:
            self.fetch_and_save_missing_ohlc()
        return self.load_dataframe_from_db()

    def load_dataframe_from_db(self):
        df = pd.DataFrame(columns = ('Date','Open','High','Low','Close', 'Adj Close', 'Volume'))
        df.set_index(keys='Date', drop=True, inplace=True)
        for point in self.stockpoints:
            df.loc[point.date] =[point.open,point.high,point.low,point.close,point.adj_close,point.volume]
        return df

    def _save_dataframe(self,df): 
        '''
        Saves a dataframe
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
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    date = db.Column(db.Date)
    open = db.Column(db.Float(precision=2,asdecimal=True))
    high = db.Column(db.Float(precision=2,asdecimal=True))
    low =  db.Column(db.Float(precision=2,asdecimal=True))
    close = db.Column(db.Float(precision=2,asdecimal=True))
    adj_close = db.Column(db.Float(precision=2,asdecimal=True))
    volume = db.Column(db.Integer)
    rsi = db.Column(db.Float(precision=2,asdecimal=True))
    macd = db.Column(db.Float(precision=2,asdecimal=True))
    macd_signal = db.Column(db.Float(precision=2,asdecimal=True))
        
    def __init__(self, date=date, open=open, high=high,
                 low=low, close=close, adj_close=adj_close, volume=volume):
        self.date, self.open, self.high, self.low, self.close, self.adj_close, self.volume = date, open, high, low, close, adj_close, volume

    @staticmethod
    def last_known_date():
        return StockPoint.query.order_by(StockPoint.date.desc()).first().date

    def __repr__(self):
        return "<StockPoint(id='%s', stock_id='%s', date='%s', open='%s', \
            high='%s', low='%s', close='%s', adj_close='%s', volume='%s', rsi='%s')>" % \
            (self.id, self.stock_id, self.date, self.open, self.high, self.low, self.close, self.adj_close, self.volume, self.rsi)
