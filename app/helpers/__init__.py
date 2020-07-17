import time
from urllib.parse import urlparse

import boto3.exceptions as boto3_exc
import werkzeug.exceptions as exc

from boto3.dynamodb.conditions import Key

from app.models.dynamo_db import get_dynamodb_table
from app import app
config = app.config


def check_params(scheme, host, url):
    if url is None:
        raise exc.BadRequest('url parameter missing from request')
    hostname = urlparse(url).hostname
    if hostname is None:
        raise exc.BadRequest('Could not determine the query hostname')
    domain = ".".join(hostname.split(".")[-2:])
    if domain not in config['allowed_domains'] and hostname not in config['allowed_hosts']:
        raise exc.BadRequest(f'Shortener can only be used for {config["allowed_domains"]} domains or '
                             f'{config["allowed_hosts"]} hosts')



def create_url(table, url):
    """
    This function creates an id which will act as the shortened url and returns it

    raise Exceptions when there is an issue during the dynamoo db table write

    :param table: the aws table on which we will write
    :param url: the url we want to shorten
    :return: the shortened url id
    """
    try:
        # we create a magic number based on epoch for our shortened_url id
        t = int(time.time() * 1000) - 1000000000000
        shortened_url = '%x' % t
        now = time.localtime()
        table.put_item(
            Item={
                'url_short': shortened_url,
                'url': url,
                'timestamp': time.strftime('%Y-%m-%d %X', now),
                'epoch': time.strftime('%s', now)
            }
        )
        return shortened_url
    # Those are internal server error: error code 500
    except boto3_exc.Boto3Error as e:
        raise exc.InternalServerError('Write units exceeded: %s' % e)
    except Exception as e:
        raise exc.InternalServerError('Error during put item %s' % e)


def fetch_url(url_id):
    url_short = url_id

    if url_short == 'toolong': # TODO: correct redirect
        raise exc.HTTPFound(location='http://map.geo.admin.ch')

    table_name = config['aws_table_name']
    aws_region = config['aws_region']

    try:
        table = get_dynamodb_table(table_name=table_name, region=aws_region)
    except Exception as e:
        raise exc.HTTPInternalServerError('Error during connection %s' % e)

    try:
        response = table.query(
            KeyConditionExpression=Key('url_short').eq(url_short)
        )
        url = response['Items'][0]['url'] if len(response['Items']) > 0 else None

    except Exception as e:  # pragma: no cover
        raise exc.HTTPInternalServerError('Unexpected internal server error: %s' % e)
    if url is None:
        raise exc.HTTPNotFound('This short url doesn\'t exist: s.geo.admin.ch/%s' % url_short)
    raise exc.HTTPMovedPermanently(location=url)


def add_item(url):
    """
    This function set a connection to a table, checks if the shortened url exists, creates it if that is not the case
    and returns the shortened url

    Each method called might raise exceptions, but this is not managed here.

    :param url: the url we want to shorten
    :return: the shortened url id
    """
    table = get_dynamodb_table(config['aws_table_name'], config['aws_region'])
    shortened_url = _check_and_get_url_short(table, url)
    if shortened_url is None:
        shortened_url = create_url(table, url)
    return shortened_url


def _check_and_get_url_short(table, url):

    response  = table.query(
        IndexName="UrlIndex",
        KeyConditionExpression=Key('url').eq(url),
    )
    try:
        return response['Items'][0]['url_short']
    except Exception:
        return None
