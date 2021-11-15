import logging
import logging.config
import os
from itertools import chain

import yaml

logger = logging.getLogger(__name__)


def get_logging_cfg():
    cfg_file = os.getenv('LOGGING_CFG', 'logging-cfg-local.yaml')

    config = {}
    with open(cfg_file, 'rt', encoding='utf-8') as fd:
        config = yaml.safe_load(fd.read())

    logger.debug('Load logging configuration from file %s', cfg_file)
    return config


def init_logging():
    config = get_logging_cfg()
    logging.config.dictConfig(config)


def get_registered_method(app, endpoint):
    '''Returns the list of registered method for the given endpoint'''

    # The list of registered method is taken from the werkzeug.routing.Rule. A Rule object
    # has a methods property with the list of allowed method on an endpoint. If this property is
    # missing then all methods are allowed.
    # See https://werkzeug.palletsprojects.com/en/2.0.x/routing/#werkzeug.routing.Rule
    all_methods = ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'DELETE']
    return list(
        chain.from_iterable([
            r.methods if r.methods else all_methods for r in app.url_map.iter_rules(endpoint)
        ])
    )


def get_redirect_param(request):
    return request.args.get('redirect', 'true')
