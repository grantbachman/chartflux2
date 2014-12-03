from app import app, db
from app.models import Stock, StockPoint, today
import datetime as dt
import locale
from flask import render_template, request, abort, jsonify
from collections import defaultdict

locale.setlocale(locale.LC_ALL, 'en_US') # for grouping large numbers with commas

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e), 404

@app.route('/')
def index():
    #fifty_two_high = Stock.find_52_week_highs()
    #fifty_two_low = Stock.find_52_week_lows()
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
def number_filter(val):
    ''' Jinja2 filter that'll filter a large int to include commas '''
    return locale.format("%d", val, grouping=True) if val is not None else 'N/A'

@app.route('/chart')
def chart():
    symbol = request.args.get('symbol').upper()
    try:
        stock = Stock.query.filter(Stock.symbol == symbol).first()
        point = stock.stockpoints[-1]
    except:
        abort(404, 'Something went wrong retrieving the data for %s' % symbol)
    if point is None:
        abort(404, 'Uh, we know that symbol, but don\'t have any data for it...')
    # group signals by whether they are buy or sell
    signals = defaultdict(list)
    for sig in stock.signals:
        if sig.expiration_date >= today():
            signals[sig.is_buy_signal].append(sig)
    signals['Buy'] = signals[True]
    signals['Sell'] = signals[False]
    del signals[True]
    del signals[False]
    if len(signals['Buy']) == len(signals['Sell']):
        recommend = 'None'
    elif len(signals['Buy']) > len(signals['Sell']):
        recommend = 'Buy'
    else:
        recommend = 'Sell'
    return render_template('chart.html',
                           stock=stock,
                           point=point,
                           signals=signals,
                           recommend=recommend
                           )
