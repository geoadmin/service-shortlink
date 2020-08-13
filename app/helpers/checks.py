import time
from urllib.parse import urlparse

import boto3.exceptions as boto3_exc
from flask import abort
from boto3.dynamodb.conditions import Key

from app.models.dynamo_db import get_dynamodb_table
from app import app
config = app.config

def check_params(scheme, host, url):
    if url is None:
        abort(400, 'url parameter missing from request')
    hostname = urlparse(url).hostname
    if hostname is None:
        abort(400, 'Could not determine the query hostname')
    domain = ".".join(hostname.split(".")[-2:])
    if domain not in config['allowed_domains'] and hostname not in config['allowed_hosts']:
        abort(400, f'Service shortlink can only be used for {config["allowed_domains"]} domains or '
                   f'{config["allowed_hosts"]} hosts')
    if host not in config['allowed_hosts']:
        host_url = make_api_url(request) + '/shorten/'
    else:
        host_url = ''.join((request.scheme, '://s.geo.admin.ch/'))

    return ''.join([scheme, host_url])