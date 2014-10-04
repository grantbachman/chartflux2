#added these
from celery.schedules import crontab
import datetime as dt

import time
from celery import Celery
from ftplib import FTP
celery = Celery('tasks')
#celery.config_from_object('app.celeryconfig')
from models import Stock
import os

celery.conf.CELERY_BROKER = 'amqp://'
celery.conf.CELERY_BACKEND = 'amqp'
celery.conf.CELERY_TIMEZONE = 'UTC'

# THIS IS UTC TIME!!!
HOUR = 17 
MINUTE = 28

# READ THIS...
#
# Start the broker.
# rabbitmq-server is located in /usr/local/sbin
# /usr/local/sbin/rabbitmq-server -detached
#
# Start Celery from the ~/Code/python/cf2 directory
# celery -A tasks worker --loglevel=info -B

celery.conf.CELERYBEAT_SCHEDULE =  {
    'download_stock_files': {
        'task': 'tasks.download_stock_files',
        'schedule': crontab(hour=HOUR,minute=MINUTE)
    },

    'parse_stock_files': {
        'task': 'tasks.parse_stock_files',
        'schedule': crontab(hour=HOUR,minute=MINUTE+1)
    }
}

@celery.task
def download_stock_files(): 
    print("Downloading stock files...")
    ftp = FTP('ftp.nasdaqtrader.com') 
    ftp.login()
    ftp.cwd('symboldirectory')
    ftp.retrbinary('RETR nasdaqlisted.txt', open('app/static/symbols/nasdaqlisted.txt', 'wb').write) 
    ftp.retrbinary('RETR otherlisted.txt', open('app/static/symbols/otherlisted.txt', 'wb').write) 
    print("Files downloaded.")

@celery.task
def parse_stock_files():
    print("Fetching stock data") 
    "File information here: http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs"
    parse_nasdaq()
    parse_other()

def parse_nasdaq():
    path = os.path.join(os.path.dirname(__file__),'static/symbols/nasdaqlisted.txt')
    with open(path, 'r') as inFile:        
        next(inFile) # ignore header
        for line in inFile:
            time.sleep(1)
            split= line.strip('\n').split('|')
            # if it's not a test stock and not the last line
            if split[3] != "Y" and "File Creation Time" not in split[0]:
                symbol = split[0]
                name = split[1]
                print("Fetching NASDAQ data for " + name + " [" + symbol + "]")
                stock = Stock.query.filter(Stock.symbol == symbol,
                                           Stock.market=='NASDAQ').first()
                if stock is None:
                    stock = Stock(symbol=symbol,name=name,market="NASDAQ")
                df = stock.get_dataframe()

def parse_other():
    path = os.path.join(os.path.dirname(__file__),'static/symbols/otherlisted.txt')
    with open(path, 'r') as inFile:        
        next(inFile) # ignore header
        for line in inFile:
            time.sleep(1)
            split= line.strip('\n').split('|')
            # if it's not a test stock and not the last line
            if split[6] != "Y" \
            and "File Creation Time" not in split[0] \
            and split[2] == 'N': # only NYSE right now
                symbol = split[7]
                name = split[1]
                print("Fetching NYSE data for " + name + " [" + symbol + "]")
                stock = Stock.query.filter(Stock.symbol == symbol,
                                           Stock.market=='NYSE').first()
                if stock is None:
                    stock = Stock(symbol=symbol,name=name,market="NYSE")
                df = stock.get_dataframe()
