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
from service_config import Config

logger = logging.getLogger(__name__)

base_response_headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTION',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-requested-with, Origin, Accept'
}


@app.route('/checker', ['GET'])
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
    logger.info(f"Checker route entered at {time.time()}")
    return make_response(jsonify({'success': True, 'message': 'OK'}))


@app.route('/shorten', ['POST'])
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
    logger.info(f"Shortlink Creation route entered at {time.time()}")
    r = request
    if r.headers.get('Origin') is None or not \
            re.match(Config.allowed_domains_pattern, request.headers['Origin']):
        logger.critical("Shortlink Error: Invalid Origin")
        abort(make_error_msg(403, "Not Allowed"))
    response_headers = base_response_headers
    url = r.json.get('url', None)
    scheme = r.scheme
    domain = r.url_root.replace(scheme, '')  # this will return the root url without the scheme
    base_path = r.script_root
    logger.debug(f"params received are : url --> {url}, scheme --> {scheme}, "
                 f"domain --> {domain}, base_path --> {base_path}")
    base_response_url = check_params(scheme, domain, url, base_path)
    response = make_response(jsonify({
        "shorturl": ''.join(base_response_url + add_item(url)),
        'success': True
    }))
    response_headers['Access-Control-Allow-Origin'] = r.headers['origin']
    response_headers['Access-Control-Allow-Methods'] = 'POST, OPTION'
    response_headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization,' \
                                                       ' x-requested-with, Origin, Accept'
    logger.info(f"Shortlink Creation Successful. Returning the following response: {str(response)}")
    response.headers.set(response_headers)
    return response


@app.route('/redirect/<shortened_url_id>', ['GET'])
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
    logger.info(f"Entry in redirection at {time.time()} with url_id {url_id}")
    url = fetch_url(url_id)
    logger.info(f"redirecting to the following url : {url}")
    return redirect(url)


@app.route('/<shortened_url_id>', ['GET'])
def fetch_full_url_from_shortlink(url_id):
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
    logger.info(f"Entry in url fetch at {time.time()} with url_id {url_id}")
    url = fetch_url(url_id)
    logger.info(f"fetched the following url : {url}")
    response = make_response(jsonify({'shorturl': url_id, 'full_url': url, 'success': True}))
    response.headers.set(base_response_headers)
    return response
