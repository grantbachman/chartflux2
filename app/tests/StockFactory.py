from app.models import Stock
from pandas import DataFrame, DatetimeIndex
import datetime as dt

def build_stock():
    return Stock(symbol='TSLA',
                 name='Tesla Motors Inc',
                 market='NASDAQ')

def build_dataframe(days=10, fill_value=1., values={}, end_date=dt.date.today(), date_index=False):
    ''' Constructs and returns a DataFrame in the form of those that
    are returned by Pandas DataReader. It doesn't take weekends or
    holidays into account, so weeked dates will generate values
    as well.
    
    Options are as follows:

    days: the number of rows to return. Defaults to 10
    fill_value: the value to fill each cell with (excluding date),
        defaults to 1
    values: A dictionary containing values with which to populate
        columns of the new dataframe.
        For example: values={'Adj Close': [5,6,7,8,9,10]}
        When one or more columns are specified, the number of rows in
        the new dataframe will be the length of the short column.
    end_date: The end of the range of dates comprising the
        dataframe. Takes a datetime.date. The start date is derived
        from a combination of this and the days parameter. Defaults to
        today's date.
    date_index: A boolean flag of whether the returned dataframe should
        set the date as the index (instead of the default numerical 
        index). If true, the dataframe will perfectly mimic that which
        is returned by Pandas DataReader.

    In addition, you may specify a non OHLC column, such as RSI, and
    it will be added to the typical OHLC dataframe that gets created.
    '''
    # some preprocessing
    columns = ['Open','High','Low','Close','Adj Close','Volume']


    # determine the minimum number of rows in values
    if len(values) > 0:
        # create a helper list of key/len(value) tuples
        helper = [(key, len(value)) for key, value in values.items()]
        helper.sort(key=lambda x: x[1])
        days = helper[0][1]
    else:
        ''' For some rason, values persisted across function calls
        when not declaring inside the function. I thought scoping
        rules would've deleted it after the function call, but I guess
        function parameters aren't killed?
        '''
        values = {} 
    for i in columns:
        if i in values:
            values[i] = values[i][:days] 
        else:
            values[i] = [fill_value] * days

    dateList = [end_date - dt.timedelta(days=i) for i in range(days)]
    # necessary so the dataframe flows from oldest to most recent when
    # read from top to bottom, like DataReader
    dateList.reverse()  
    values['Date'] = DatetimeIndex(dateList)
    df = DataFrame(values, index=range(days))
    if date_index == True:
        df.set_index(keys='Date', drop=True, inplace=True)
    return df
