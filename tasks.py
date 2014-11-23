import logging
from celery.schedules import crontab
import datetime as dt

import time
from celery import Celery
from ftplib import FTP
celery = Celery('tasks')

from app.models import Stock
import os, sys

celery.conf.CELERY_BROKER = 'amqp://'
celery.conf.CELERY_BACKEND = 'amqp'
celery.conf.CELERY_TIMEZONE = 'UTC'

# THIS IS UTC TIME, which is +4 hours of EST
HOUR = 16  
MINUTE = 10

# READ THIS...
#
# Start the broker.
# rabbitmq-server is located in /usr/local/sbin
# /usr/local/sbin/rabbitmq-server -detached
#
# Start Celery from the ~/Code/python/cf2 directory
# celery -app=tasks worker --loglevel=info -B

celery.conf.CELERYBEAT_SCHEDULE =  {
    'download_stock_files': {
        'task': 'tasks.download_stock_files',
        'schedule': crontab(hour=HOUR,minute=MINUTE)
    },
    'parse_stock_files': {
        'task': 'tasks.parse_stock_files',
        'schedule': crontab(hour=HOUR,minute=MINUTE+1)
    }
    #'calculate_indicators': {
    #    'task': 'tasks.calculate_indicators',
    #    'schedule': crontab(hour=HOUR,minute=MINUTE)
    #}
}

@celery.task
def download_stock_files(): 
    logging.info('Begin downloading stock files...')
    try:
        ftp = FTP('ftp.nasdaqtrader.com') 
        ftp.login()
        ftp.cwd('symboldirectory')
        ftp.retrbinary('RETR nasdaqlisted.txt', open('app/static/symbols/nasdaqlisted.txt', 'wb').write) 
        ftp.retrbinary('RETR otherlisted.txt', open('app/static/symbols/otherlisted.txt', 'wb').write) 
        logging.info('Finished downloading stock files.')
    except Exception as e:
        logging.warning("Couldn't download the nightly NASDAQ/NYSE files. Error message: %s", e)

@celery.task
def parse_stock_files():
    '''File information here: http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs'''
    logging.info('Begin parsing the files and refreshing stock data.')
    parse_nasdaq('NASDAQ')
    parse_other('NYSE')
    logging.info('Finished parsing the files and refreshing stock data.')

def parse_nasdaq(market):
    logging.info('Begin parsing %s file.', market)
    path = os.path.join(os.path.dirname(__file__),'app/static/symbols/nasdaqlisted.txt')
    with open(path, 'r') as inFile:        
        next(inFile) # ignore header
        for line in inFile:
            #time.sleep(1)
            split= line.strip('\r\n').split('|')
            # if it's not a test stock and not the last line
            if split[3] != "Y" and "File Creation Time" not in split[0]:
                symbol = split[0]
                name = split[1]
                logging.info('Fetching data. Market: %s, Symbol: %s, Company Name: %s', market, symbol, name)
                create_or_update_stock(symbol, name, market)
    logging.info('Finished parsing %s file.', market)

def create_or_update_stock(symbol, name, market):
    stock = Stock.query.filter(Stock.symbol == symbol,
                               Stock.market=='NASDAQ').first()
    if stock is None:
        logging.info('New stock (not currently in our database): Market: %s, Symbol: %s, Company Name: %s', market, symbol, name)
        stock = Stock(symbol=symbol,name=name,market="NASDAQ")
    df = stock.get_dataframe()
    if df is None or len(df) == 0:
        logging.warning('Error retrieving Stock from the database (DataFrame is empty...): Stock.id: %s, Market: %s, Symbol: %s, Company Name: %s', stock.id, market, symbol, name)
    else:
        stock.calculate_indicators()


@celery.task
def calculate_indicators():
    logging.info('Begin Calculating indicators for all stocks.')
    for stock in Stock.query.all():
        logging.info('Updating indicators for %s [%s]', stock.symbol, stock.name)
        stock.calculate_indicators()

def parse_other(market):
    logging.info('Begin parsing %s file.', market)
    path = os.path.join(os.path.dirname(__file__),'app/static/symbols/otherlisted.txt')
    with open(path, 'r') as inFile:        
        next(inFile) # ignore header
        for line in inFile:
            #time.sleep(1)
            split = line.strip('\r\n').split('|')
            # if it's not a test stock and not the last line
            if 'File Creation Time' not in split[0] and split[2] == 'N' and split[6] != 'Y':
                symbol = split[7]
                name = split[1]
                logging.info('Fetching data. Market: %s, Symbol: %s, Company Name: %s', market, symbol, name)
                create_or_update_stock(symbol, name, market)
    logging.info('Finished parsing %s file.', market)


