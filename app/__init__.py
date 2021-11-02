import logging
import re

from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import Flask
from flask import abort
from flask import request

from app.helpers import init_logging
from app.helpers.response_generation import make_error_msg
from service_config import ALLOWED_DOMAINS_PATTERN

#initialize logging using JSON as a format.
init_logging()

logger = logging.getLogger(__name__)

# Standard Flask application initialisation

app = Flask(__name__)
app.config.from_mapping({"TRAP_HTTP_EXCEPTIONS": True})


# Reject request from non allowed origins
@app.before_request
def validate_origin():
    if 'Origin' not in request.headers:
        logger.error('Origin header is not set')
        abort(403, 'Permission denied')
    if not re.match(ALLOWED_DOMAINS_PATTERN, request.headers['Origin']):
        logger.error('Origin %s is not allowed', request.headers['Origin'])
        abort(403, 'Permission denied')


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
