from app import app
from flask import request, Response, redirect
from app.helpers import  add_item, check_params, fetch_url


@app.route('/checker', ['GET'])
@app.route('/checker/', ['GET'])
def checker():
    return 'OK', 200


"""
The shorten route's goal is to take an url and create a shortlink to it.
The only parameter we should receive is the url to be shortened.
In the route, we check the url received for the following comportments : [SHORTENED_URL]
if the url is not from an allowed host or domain, we refuse it. 
https://github.com/geoadmin/mf-chsdi3/blob/a75335af46f156f7ad9c10efe17eb52c888d671b/chsdi/lib/helpers.py#L130
we also check from who the query comes, and here is the expected comportment: [HOST]
if it comes from the api, the redirection host becomes s.geo.admin.ch
if it comes from somewhere else (for example: if we deploy the service in a test environment) : 
https://github.com/geoadmin/mf-chsdi3/blob/a75335af46f156f7ad9c10efe17eb52c888d671b/chsdi/lib/helpers.py#L105
host = request.host + ('' if [dev, int, prod] else '/user_name) if host is not Localhost, else localhost
if agnostic: return ''.join(('//', host) --> //boulgour.admin.ch
else return ''.joins(request.scheme, '://', host) --> https://boulgour.admin.ch

final result --> [HOST + SHORTENED_URL]
"""


@app.route('/shorten', ['GET'])
@app.route('/shorten/', ['GET'])
@app.route('/shorten.json', ['GET'])
@app.route('/shorten.json/', ['GET'])
def shorten():
    response_headers = {'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-requested-with, Origin, Accept',
                        'Max-Age': '5'}
    r = request
    url = r.args.get('url', None)
    scheme = r.scheme
    domain = r.url_root.replace(scheme, '')  # this will return the root url without the scheme
    base_response_url = check_params(scheme, domain, url)
    shortened_id = add_item(url)
    response = {"shorturl": base_response_url + str(shortened_id)}
    return response, 200, response_headers


@app.route('/redirect/<shortened_url_id>', ['GET'])
@app.route('/redirect/<shortened_url_id>/', ['GET'])
def shorten_redirect(url_id):
    response_headers = {'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-requested-with, Origin, Accept',
                        'Max-Age': '5'}
    url = fetch_url(url_id)
    return redirect(url, code='302')
