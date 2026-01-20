import logging
import logging.config
import os
import re
from itertools import chain
from pathlib import Path
from urllib.parse import urlparse

import validators
import yaml
from nanoid import generate

from flask import abort
from flask import jsonify
from flask import make_response
from flask import request

from app.helpers.otel import strtobool
from app.settings import ALLOWED_DOMAINS_PATTERN
from app.settings import SHORT_ID_ALPHABET
from app.settings import SHORT_ID_SIZE

logger = logging.getLogger(__name__)


def get_logging_cfg():
    cfg_file = os.getenv('LOGGING_CFG', 'logging-cfg-local.yaml')
    if 'LOGS_DIR' not in os.environ:
        # Build paths inside the project like this: BASE_DIR / 'subdir'.
        logs_dir = Path(__file__).resolve(strict=True).parent.parent.parent / 'logs'
        os.environ['LOGS_DIR'] = str(logs_dir)
    print(f"LOGS_DIR is {os.environ['LOGS_DIR']}")
    print(f"LOGGING_CFG is {cfg_file}")

    config = {}
    with open(cfg_file, 'rt', encoding='utf-8') as fd:
        config = yaml.safe_load(os.path.expandvars(fd.read()))

    logger.debug('Load logging configuration from file %s', cfg_file)
    return config


def init_logging():
    config = get_logging_cfg()
    logging.config.dictConfig(config)


def get_registered_method(app, url_rule):
    '''Returns the list of registered method for the given endpoint'''

    # The list of registered method is taken from the werkzeug.routing.Rule. A Rule object
    # has a methods property with the list of allowed method on an endpoint. If this property is
    # missing then all methods are allowed.
    # See https://werkzeug.palletsprojects.com/en/2.0.x/routing/#werkzeug.routing.Rule
    all_methods = ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'DELETE']
    return set(
        chain.from_iterable([
            r.methods if r.methods else all_methods
            for r in app.url_map.iter_rules()
            if r.rule == str(url_rule)
        ])
    )


def get_redirect_param(ignore_errors=False):
    try:
        redirect = strtobool(request.args.get('redirect', 'true'))
    except ValueError as error:
        redirect = False
        if not ignore_errors:
            abort(400, f'Invalid "redirect" arg: {error}')
    return redirect


def generate_short_id():
    return generate(SHORT_ID_ALPHABET, SHORT_ID_SIZE)


def make_error_msg(code, msg):
    response = make_response(
        jsonify({
            'success': False, 'error': {
                'code': code, 'message': msg
            }
        }),
        code,
    )
    return response


def get_url():
    """
    Get and check the url parameter

    Abort with a 400 status code if there is no url, given to shorten
    Abort with a 400 status code if the url is over 2046 characters long (dynamodb limitation)
    Abort with a 400 status code if the hostname of the URL parameter is not allowed.
    Abort with a 415 status code if the payload is invalid.
    """
    if not request.is_json:
        abort(415, 'Input data missing or from wrong type, must be application/json')
    url = request.get_json().get('url', None)
    if url is None:
        logger.error('"url" parameter missing from input json')
        abort(400, 'Url parameter missing from request')
    if not validators.url(url):
        logger.error('URL %s not valid.', url)
        abort(400, f"URL({url}) given as parameter is not valid.")
        # urls have a maximum size of 2046 character due to a dynamodb limitation
    if len(url) > 2046:
        logger.error("Url(%s) given as parameter exceeds characters limit.", url)
        abort(
            400,
            f"The url given as parameter was too long. (limit is 2046 "
            f"characters, {len(url)} given)"
        )
    if not is_domain_allowed(url):
        logger.error(
            'URL(%s) given as a parameter is not allowed, test pattern %s',
            url,
            ALLOWED_DOMAINS_PATTERN
        )
        abort(400, 'URL given as a parameter is not allowed.')

    return url


def is_domain_allowed(url):
    """Check if the url contain a domain that is allowed
    """
    domain = urlparse(url).hostname
    if domain:
        return re.fullmatch(ALLOWED_DOMAINS_PATTERN, domain) is not None
    return False
