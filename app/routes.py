import json
import logging
import time

from flask import abort
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import request
from flask import url_for

from app import app
from app.helpers.checks import check_params
from app.helpers.urls import add_item
from app.helpers.urls import fetch_url
from app.helpers.utils import get_redirect_param
from app.models.dynamo_db import get_dynamodb_table

logger = logging.getLogger(__name__)


@app.route('/checker', methods=['GET'])
def checker():
    """
    * Quick summary of the function *

    Simple function to check if the service is alive with no call to any other functions.

    * Abortions originating in this function *

    None

    * Abortions originating in functions called from this function *

    None

    * Parameters and return values *

    :return: a simple json saying basically 'OK'
    """
    logger.debug("Checker route entered at %f", time.time())
    response = make_response(jsonify({'success': True, 'message': 'OK'}), 200)
    return response


@app.route('/', methods=['POST'])
def create_shortlink():
    """
    * Quick summary of the function *

    The create_shortlink route's goal is to take an url and create a shortlink to it.
    The only parameter we should receive is the url to be shortened, within the post payload.

    We extract the url to shorten, the request scheme, domain and base path and send them to a
    function to check those parameters. (check_params)

    If those parameters are checked, we create the response to be sent to the user and create the
    shortlink to send back (add_item)

    * Abortions originating in this function *

    Abort with a 400 status code if we do not receive a json in the post payload
    Abort with a 403 status code if the Origin header is not set nor one we expect.

    * Abortions originating in functions called from this function *

    Abort with a 400 status code from check_params
    Abort with a 500 status code from add_item

    * Parameters and return values *

    :request: the request must contain a Origin Header, and a json payload with an url field
    :return: a json in response which contains the url which will redirect to the initial url
    """
    logger.debug("Shortlink Creation route entered at %f", time.time())
    try:
        url = request.json.get('url', None)
    except AttributeError as err:
        logger.error("No Json Received as parameter : %s", err)
        abort(400, "This service requires a json to be posted as a payload.")
    except json.decoder.JSONDecodeError:
        logger.error("Invalid Json Received as parameter")
        abort(400, "The json received was malformed and could not be interpreted as a json.")
    logger.debug("params received are : url: %s", url)
    check_params(url)
    table = get_dynamodb_table()
    shortlink_id = add_item(table, url)
    response = make_response(
        jsonify({
            "shorturl": url_for("get_shortlink", shortlink_id=shortlink_id, _external=True),
            'success': True
        })
    )

    logger.info(
        "Shortlink Creation Successful.", extra={"response": json.loads(response.get_data())}
    )
    return response


@app.route('/<shortlink_id>', methods=['GET'])
def get_shortlink(shortlink_id):
    """
    * Quick summary of the function *

    This route checks the shortened url id  and redirect the user to the full url.
    When the redirect query parameter is set to false, it will return a json containing
    the information about the url.

    * Abortions originating in this function *

    None

    * Abortions originating in functions called from this function *

    Abort with a 400 error if the redirect parameter is set to a fantasist value
    Abort with a 404 error from fetch_url
    Abort with a 500 error from fetch_url

    * Parameters and return values *

    :param shortlink_id: a short url id
    :return: a redirection to the full url or a json with the full url
    """
    logger.debug("Entry in shortlinks fetch at %f with url_id %s", time.time(), shortlink_id)
    should_redirect = get_redirect_param(request)
    if should_redirect not in ("true", "false"):
        logger.error("redirect parameter set to a non accepted value : %s", should_redirect)
        abort(400, "accepted values for redirect parameter are true or false.")
    logger.debug("Redirection is set to : %s ", str(should_redirect))
    table = get_dynamodb_table()
    url = fetch_url(table, shortlink_id, request.base_url)
    if should_redirect == 'true':
        logger.info("redirecting to the following url : %s", url)
        return redirect(url, code=301)
    logger.info("fetched the following url : %s", url)
    response = make_response(jsonify({'shorturl': shortlink_id, 'full_url': url, 'success': True}))
    return response
