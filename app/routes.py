import re
import logging
import time

from flask import abort
from flask import jsonify
from flask import make_response
from flask import request
from flask import redirect

from app import app
from app.helpers import add_item
from app.helpers import fetch_url
from app.helpers.checks import check_params
from app.helpers.response_generation import make_error_msg
from app.models.dynamo_db import get_dynamodb_table
from service_config import Config

logger = logging.getLogger(__name__)

base_response_headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTION',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-requested-with, Origin, Accept'
}


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
    logger.info("Checker route entered at %f", str(time.time()))
    return make_response(jsonify({'success': True, 'message': 'OK'}))


@app.route('/shorten', methods=['POST'])
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

    Abort with a 403 status code if the Origin header is not set nor one we expect.

    * Abortions originating in functions called from this function *

    Abort with a 400 status code from check_params, add_item
    Abort with a 500 status code from add_item

    * Parameters and return values *

    :request: the request must contain a Origin Header, and a json payload with an url field
    :return: a json in response which contains the url which will redirect to the initial url
    """
    logger.info("Shortlink Creation route entered at %f", time.time())
    if request.headers.get('Origin') is None or not \
            re.match(Config.allowed_domains_pattern, request.headers['Origin']):
        logger.critical("Shortlink Error: Invalid Origin")
        abort(make_error_msg(403, "Not Allowed"))
    response_headers = base_response_headers
    url = request.json.get('url', None)
    scheme = request.scheme
    domain = request.url_root.replace(
        scheme, ''
    )  # this will return the root url without the scheme
    base_path = request.script_root
    logger.debug(
        "params received are : url: %s, scheme: %s, domain: %s, base_path: %s",
        url, scheme, domain, base_path
    )
    base_response_url = check_params(scheme, domain, url, base_path)
    table = get_dynamodb_table()
    response = make_response(
        jsonify({
            "shorturl": ''.join(base_response_url + add_item(table, url)), 'success': True
        })
    )
    response_headers['Access-Control-Allow-Origin'] = request.headers['origin']
    response_headers['Access-Control-Allow-Methods'] = 'POST, OPTION'
    response_headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization,' \
                                                       ' x-requested-with, Origin, Accept'
    logger.info(
        "Shortlink Creation Successful. Returning the following response: %s", str(response)
    )
    response.headers.set(response_headers)
    return response


@app.route('/redirect/<url_id>', methods=['GET'])
def redirect_shortlink(url_id):
    """
    * Quick summary of the function *

    This route checks the shortened url id  and redirect the user to the full url

    * Abortions originating in this function *

    None

    * Abortions originating in functions called from this function *

    Abort with a 404 error from fetch_url
    Abort with a 500 error from fetch_url

    * Parameters and return values *

    :param url_id: a short url id
    :return: a redirection to the full url
    """
    logger.info("Entry in redirection at %f with url_id %s", time.time(), url_id)
    table = get_dynamodb_table()
    url = fetch_url(table, url_id, request.url_root)
    logger.info("redirecting to the following url : %s", url)
    return redirect(url)


@app.route('/<shortened_url_id>', methods=['GET'])
def fetch_full_url_from_shortlink(shortened_url_id):
    """
    * Quick summary of the function *

    This route checks the shortened url id  and returns a json containing both the shortened url and
    the full url

    * Abortions originating in this function *

    None

    * Abortions originating in functions called from this function *

    Abort with a 404 error from fetch_url
    Abort with a 500 error from fetch_url

    * Parameters and return values *

    :param url_id: a short url id
    :return: a json with the full url
    """
    logger.info("Entry in url fetch at %f with url_id %s", time.time(), shortened_url_id)
    table = get_dynamodb_table()
    url = fetch_url(table, shortened_url_id, request.url_root)
    logger.info("fetched the following url : %s", url)
    response = make_response(jsonify({'shorturl': shortened_url_id, 'full_url': url, 'success': True}))
    response.headers.set(base_response_headers)
    return response
