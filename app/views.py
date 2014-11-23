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

@app.template_filter('ohlc')
def ohlc_filter(val):
    ''' Jinja2 filter that'll format a float with exactly 2 decimal
    place precision. If the value is None it'll return N/A '''
    return format(val, '.2f') if val is not None else 'N/A'

@app.template_filter('volume')
def ohlc_filter(val):
    ''' Jinja2 filter that'll filter a large int to include commas '''
    return locale.format("%d", val, grouping=True) if val is not None else 'N/A'

@app.route('/chart')
def chart():
    symbol = request.args.get('symbol').upper()
    try:
        point = db.session.query(StockPoint,Stock).filter(Stock.id == StockPoint.stock_id).filter(Stock.symbol == symbol).order_by(StockPoint.date.desc()).first()
    except:
        abort(404, 'We could\'t find that stock for some reason. Right now we only have data for the NASDAQ and NYSE. If the stock you entered WAS in either of those exchanges, well, then we done fucked up.')
    if point is None:
        abort(404, 'Uh, we know that symbol, but don\'t have any data for it...')
    return render_template('chart.html', point=point)
