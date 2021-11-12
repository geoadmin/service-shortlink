import logging
import re

from werkzeug.exceptions import HTTPException

from flask import Flask
from flask import abort
from flask import request
from flask import url_for

from app.helpers.response_generation import make_error_msg
from app.helpers.utils import get_redirect_param
from app.helpers.utils import get_registered_method
from app.settings import ALLOWED_DOMAINS_PATTERN
from app.settings import CACHE_CONTROL
from app.settings import CACHE_CONTROL_4XX

logger = logging.getLogger(__name__)

# Standard Flask application initialisation

app = Flask(__name__)
app.config.from_mapping({"TRAP_HTTP_EXCEPTIONS": True})


# Reject request from non allowed origins
@app.before_request
def validate_origin():
    if request.endpoint == 'get_shortlink' and get_redirect_param(request) == 'true':
        # Don't validate the origin for the get_shortlink endpoint with redirect.
        # The main purpose of this endpoint is to share a link, so this link may be used by
        # any origin (anyone)
        return

    if 'Origin' not in request.headers:
        logger.error('Origin header is not set')
        abort(403, 'Permission denied')
    if not re.match(ALLOWED_DOMAINS_PATTERN, request.headers['Origin']):
        logger.error('Origin %s is not allowed', request.headers['Origin'])
        abort(403, 'Permission denied')


@app.after_request
def add_charset(response):
    # Python uses UTF-8 as charset by default
    if response.headers.get('Content-Type') == 'application/json':
        response.headers.set('Content-Type', 'application/json; charset=utf-8')
    return response


# Add CORS Headers to all request
@app.after_request
def add_generic_cors_header(response):
    if (
        'Origin' in request.headers and
        re.match(ALLOWED_DOMAINS_PATTERN, request.headers['Origin'])
    ):
        # Don't add the allow origin if the origin is not allowed, otherwise that would give
        # a hint to the user on how to missused this service
        response.headers.set('Access-Control-Allow-Origin', request.headers['Origin'])
    # Always add the allowed methods.
    response.headers.set(
        'Access-Control-Allow-Methods', ', '.join(get_registered_method(app, request.endpoint))
    )
    response.headers.set('Access-Control-Allow-Headers', '*')
    return response


@app.after_request
def add_cache_control_header(response):
    # For /checker route we let the frontend proxy decide how to cache it.
    if request.method == 'GET' and request.path != url_for('checker'):
        if response.status_code >= 400:
            response.headers.set('Cache-Control', CACHE_CONTROL_4XX)
        else:
            response.headers.set('Cache-Control', CACHE_CONTROL)
    return response


# Register error handler to make sure that every error returns a json answer
@app.errorhandler(Exception)
def handle_exception(err):
    """Return JSON instead of HTML for HTTP errors."""
    if isinstance(err, HTTPException):
        logger.error(err)
        return make_error_msg(err.code, err.description)

    logger.exception('Unexpected exception: %s', err)
    return make_error_msg(500, "Internal server error, please consult logs")


from app import routes  # isort:skip pylint: disable=ungrouped-imports, wrong-import-position
