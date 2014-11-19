from app import app, db
from app.models import Stock, StockPoint, today
import datetime as dt
import locale
from flask import render_template, request, abort, jsonify

locale.setlocale(locale.LC_ALL, 'en_US') # for grouping large numbers with commas

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e), 404

@app.route('/')
def index():
    buy_stocks = Stock.find_buy_stocks()
    sell_stocks = Stock.find_sell_stocks()
    return render_template('index.html',
                           buy_stocks=buy_stocks,
                           sell_stocks=sell_stocks)

@app.route('/chart')
def chart():
    symbol = request.args.get('symbol').upper()
    try:
        point = db.session.query(StockPoint,Stock).filter(Stock.id == StockPoint.stock_id).filter(Stock.symbol == symbol).filter(StockPoint.date == StockPoint.last_known_date()).first()
    except:
        abort(404, 'We could\'t find that stock for some reason. Right now we only have data for the NASDAQ and NYSE. If the stock you entered WAS in either of those exchanges, well, then we done fucked up.')
    change = format(point[0].close - point[0].open, '.2f')
    change_percent = format((point[0].close - point[0].open)/point[0].open*100, '.2f')
    change_tup = tuple([change, change_percent])
    point[0].close = format(point[0].close,'.2f')
    point[0].adj_close = format(point[0].adj_close,'.2f')
    point[0].open = format(point[0].open,'.2f')
    point[0].high = format(point[0].high,'.2f')
    point[0].low = format(point[0].low,'.2f')
    point[0].rsi = format(point[0].rsi,'.2f') if point[0].rsi is not None else 'N/A'
    point[0].macd = format(point[0].macd,'.2f') if point[0].macd is not None else 'N/A'
    point[0].macd_signal = format(point[0].macd_signal,'.2f') if point[0].macd_signal is not None else 'N/A'
    point[0].volume = locale.format("%d",point[0].volume,grouping=True)
    return render_template('chart.html', point=point, change_tup=change_tup)
