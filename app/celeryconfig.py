from celery.schedules import crontab
import datetime as dt

CELERY_BROKER = 'amqp://'
CELERY_BACKEND = 'amqp'
CELERY_TIMEZONE = 'UTC'

# THIS IS UTC TIME!!!
HOUR = 0 
MINUTE = 27 

# READ THIS...
#
# Start the broker.
# rabbitmq-server is located in /usr/local/sbin
# /usr/local/sbin/rabbitmq-server -detached
#
# Start the Celery daemon from the ~/Code/python/cf2 directory
# celery -A app.tasks worker --loglevel=info --beat
# However, this isn't quite right...still need to work it out
# http://hairycode.org/2013/07/23/first-steps-with-celery-how-to-not-trip/

CELERYBEAT_SCHEDULE =  {
    'download_stock_files': {
        'task': 'download_stock_files',
        'schedule': crontab(hour=HOUR,minute=MINUTE)
    },

    'parse_stock_files': {
        'task': 'parse_stock_files',
        'schedule': crontab(hour=HOUR,minute=MINUTE+1)
    }
}

