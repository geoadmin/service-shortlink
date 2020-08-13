import re
from app import app
from flask import request, Response, redirect, abort
from app.helpers import  add_item, check_params, fetch_url, create_response
from service_config import Config


@app.route('/checker', ['GET'])
def checker():
    return 'OK', 200


"""
The create_shortlink route's goal is to take an url and create a shortlink to it.
The only parameter we should receive is the url to be shortened.
In the route, we check the url received for the following comportments : [SHORTENED_URL]
if the url is not from an allowed host or domain, we refuse it. 
https://github.com/geoadmin/mf-chsdi3/blob/a75335af46f156f7ad9c10efe17eb52c888d671b/chsdi/lib/helpers.py#L130
we also check from who the query comes, and here is the expected comportment: [HOST]
if it comes from the api, the redirection host becomes s.geo.admin.ch
if it comes from somewhere else (for example: if we deploy the service in a test environment) : 
https://github.com/geoadmin/mf-chsdi3/blob/a75335af46f156f7ad9c10efe17eb52c888d671b/chsdi/lib/helpers.py#L105
host = request.host + ('' if [dev, int, prod] else '/user_name) if host is not Localhost, else 
localhost
if agnostic: return ''.join(('//', host) --> //boulgour.admin.ch
else return ''.joins(request.scheme, '://', host) --> https://boulgour.admin.ch

final result --> [HOST + SHORTENED_URL]
"""


@app.route('/shorten', ['GET'])
@app.route('/shorten.json', ['GET'])
def create_shortlink():
    r = request
    response_headers = {'Content-Type': 'application/json; charset=utf-8'}
    url = r.args.get('url', None)
    scheme = r.scheme
    domain = r.url_root.replace(scheme, '')  # this will return the root url without the scheme
    base_response_url = check_params(scheme, domain, url)
    response = create_response(base_response_url, add_item(url))
    if r.headers.get('Origin') is not None and \
            re.match(Config.allowed_domains_pattern, request.headers['Origin']):
        response_headers['Access-Control-Allow-Origin'] = r.headers['origin']
        response_headers['Access-Control-Allow-Methods'] = 'GET, OPTION'
        response_headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization,' \
                                                           ' x-requested-with, Origin, Accept'
    return response, 200, response_headers


@app.route('/redirect/<shortened_url_id>', ['GET'])
def redirect_shortlink(url_id):
    url = fetch_url(url_id)
    return redirect(url, code='302')
