import logging

from werkzeug.exceptions import HTTPException

from flask import Flask

from app.helpers import init_logging
from app.helpers.response_generation import make_error_msg
from app.middleware import ReverseProxies

#initialize logging using JSON as a format.
init_logging()

logger = logging.getLogger(__name__)

# Standard Flask application initialisation

app = Flask(__name__)
app.config.from_mapping({"TRAP_HTTP_EXCEPTIONS": True})
app.wsgi_app = ReverseProxies(app.wsgi_app, script_name='/')


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
