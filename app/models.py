from pandas.io.data import DataReader
import pandas as pd
import datetime as dt
from app import db
from sqlalchemy.sql.expression import desc


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(8))
    name = db.Column(db.String(100))
    market = db.Column(db.String(10))    # could make this a category
    stockpoints = db.relationship('StockPoint', order_by=desc('stock_point.date'))

    LOOKBACK_DAYS = 300

    def __init__(self, symbol=symbol, name=name, market=market):
        self.symbol = symbol.upper()
        self.name = name
        self.market = market

    def get_dataframe(self):
        if not self.stockpoints:
            print('   No data found, pulling from Google')
            self.fetch_and_save_all_ohlc()
        else:
            print('   Pulling data from local storage')
            self.fetch_and_save_missing_ohlc()
        return self.load_dataframe_from_db()

    def load_dataframe_from_db(self):
        df = pd.DataFrame(columns = ('Date','Open','High','Low','Close','Volume'))
        df.set_index(keys='Date', drop=True, inplace=True)
        for point in self.stockpoints:
            df.loc[point.date] =[point.open,point.high,point.low,point.close,point.volume]
        return df

    def save_points(self,df): 
        '''
        If the stock doesn't exist, it creates it.
        Blithely saves off the rows of a dataframe to the StockPoints table
        '''
        if Stock.query.filter(Stock.symbol==self.symbol,
                              Stock.market==self.market).count() == 0:
            db.session.add(self)
        for row_index, row in df.iterrows():
            row['Date']=row['Date'].date()
            newPoint = StockPoint(date=row['Date'], open=row['Open'],
                                  high=row['High'], low=row['Low'],
                                  close=row['Close'], volume=row['Volume'])
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
        next_point_date = self.stockpoints[0].date + dt.timedelta(days=1)
        if next_point_date != dt.date.today():
            yesterday = dt.date.today() - dt.timedelta(days=1) # they never return today's data
            df = self.fetch_ohlc_from_google(next_point_date, yesterday)
            if df is not None:
                self.save_points(df)               
    
    def fetch_and_save_all_ohlc(self):
        ''' Fetches the model's maximum number of data points'''
        end_date = dt.date.today()
        start_date  = end_date - dt.timedelta(days = Stock.LOOKBACK_DAYS)
        df = self.fetch_ohlc_from_google(start_date, end_date)
        if df is not None:
            self.save_points(df)

    def fetch_ohlc_from_google(self,start_date,end_date):
        ''' Fetches data for specified dates'''
        try:
            df = DataReader(self.symbol, "google", start_date, end_date)
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
    close =  db.Column(db.Float(precision=2,asdecimal=True))
    volume = db.Column(db.Integer)

        
    def __init__(self, date=date, open=open, high=high,
                 low=low, close=close, volume=volume):
        self.date, self.open, self.high, \
        self.low, self.close, self.volume = date, open, high, low, close, volume

