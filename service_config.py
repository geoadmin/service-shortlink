import os
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


class Config(object):
    """
    The Config class contains everything needed to run the service. Most entries have a default
    value and an environment value to override it.

    """
    allowed_domains = os.environ.get('ALLOWED_DOMAINS', 'admin.ch,swisstopo.ch,bgdi.ch').split(',')
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', 'api.geo.admin.ch,api3.geo.admin.ch').split(',')
    aws_table_name = os.environ.get('AWS_DYNAMODB_TABLE_NAME', 'shortlink')
    aws_region = os.environ.get('AWS_DYNAMODB_TABLE_REGION', 'eu-west-1')
    allowed_domains_pattern = r'*\.admin\.ch|*\.swisstopo\.cloud|*\.bgdi\.ch'
