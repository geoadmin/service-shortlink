from urllib.parse import urlparse
from flask import abort
from boto3.dynamodb.conditions import Key
from app.helpers import make_api_url
from app import app
config = app.config


def check_params(scheme, host, url, base_path):
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
        host_url = make_api_url(scheme, host, base_path) + '/redirect/'
    else:
        host_url = ''.join((scheme, '://s.geo.admin.ch/'))

    return host_url


def check_and_get_url_short(table, url):

    response = table.query(
        IndexName="UrlIndex",
        KeyConditionExpression=Key('url').eq(url),
    )
    try:
        return response['Items'][0]['url_short']
    except Exception:
        return None
