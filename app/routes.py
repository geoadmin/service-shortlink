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
from app.helpers import  fetch_url
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
    logger.info(f"Checker route entered at {time.time()}")
    return make_response(jsonify({'success': True, 'message': 'OK'}))


@app.route('/shorten', ['POST'])
def create_shortlink():
    """
    The create_shortlink route's goal is to take an url and create a shortlink to it.
    The only parameter we should receive is the url to be shortened.
    In the route, we check the url received for the following comportments : [SHORTENED_URL]
    if the url is not from an allowed host or domain, we refuse it.

    final result --> [HOST + SHORTENED_URL]
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
    logger.info(f"Entry in redirection at {time.time()} with url_id {url_id}")
    url = fetch_url(url_id)
    logger.info(f"redirecting to the following url : {url}")
    return redirect(url, code='302')


@app.route('/<shortened_url_id>', ['GET'])
def fetch_full_url_from_shortlink(url_id):
    """
    This is mostly a debug route, meant to return a
    """
    logger.info(f"Entry in url fetch at {time.time()} with url_id {url_id}")
    url = fetch_url(url_id)
    logger.info(f"fetched the following url : {url}")
    response = make_response(jsonify({'shorturl': url_id, 'full_url': url, 'success': True}))
    response.headers.set(base_response_headers)
    return response
