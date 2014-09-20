from app import app
from flask import render_template, request


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chart')
def chart():
    symbol = request.args.get('symbol')
    return render_template('chart.html', symbol=symbol) 
