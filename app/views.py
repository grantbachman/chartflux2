from app import app
from flask import render_template, request


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chart')
def chart():
    stock = request.args.get('ticker')
    return render_template('chart.html', stock=stock)
