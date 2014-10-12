from app import app, db
from app.models import Stock, StockPoint, RSI, today
import datetime as dt
from flask import render_template, request


@app.route('/')
def index():
    date = today() - dt.timedelta(days=1)
    buy_stocks = Stock.find_buy_stocks()
    sell_stocks = Stock.find_sell_stocks()
    return render_template('index.html', buy_stocks=buy_stocks, sell_stocks=sell_stocks)

@app.route('/chart')
def chart():
    symbol = request.args.get('symbol')
    return render_template('chart.html', symbol=symbol) 
