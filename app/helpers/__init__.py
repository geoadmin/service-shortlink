import time
from urllib.parse import urlparse

import boto3.exceptions as boto3_exc
from flask import abort
from boto3.dynamodb.conditions import Key
from app.helpers.checks import check_and_get_url_short
from app.models.dynamo_db import get_dynamodb_table
from app import app
config = app.config


def make_api_url(request):
    pass


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
        # urls have a maximum size of 2046 character due to a dynamodb limitation
        if len(url) > 2046:
            return "toolong", \
                   f"The url given as parameter was too long. (limit is 2046, {len(url)} given)"
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
        return shortened_url, None
    # Those are internal server error: error code 500
    except boto3_exc.Boto3Error as e:
        abort(500, f"Write units exceeded: {str(e)}")
    except Exception as e:
        abort(500, f"Error during put item: {str(e)}")


def fetch_url(url_id):
    url_short = url_id

    if url_short == 'toolong':  # TODO: correct redirect
        return 'http://map.geo.admin.ch'

    table_name = config['aws_table_name']
    aws_region = config['aws_region']
    table = None
    url = None
    try:
        table = get_dynamodb_table(table_name=table_name, region=aws_region)
    except Exception as e:
        abort(500, f'Error during connection {str(e)}')

    try:
        response = table.query(
            KeyConditionExpression=Key('url_short').eq(url_short)
        )
        url = response['Items'][0]['url'] if len(response['Items']) > 0 else None

    except Exception as e:  # pragma: no cover
        abort(500, f'Unexpected internal server error: {str(e)}')
    if url is None:
        abort(404, f'This short url doesn\'t exist: s.geo.admin.ch/{str(url_id)}')
    return url


def add_item(url):
    """
    This function set a connection to a table, checks if the shortened url exists, creates it if that is not the case
    and returns the shortened url

    Each method called might raise exceptions, but this is not managed here.

    :param url: the url we want to shorten
    :return: the shortened url id
    """
    table = get_dynamodb_table(config['aws_table_name'], config['aws_region'])
    shortened_url = check_and_get_url_short(table, url)
    if shortened_url is None:
        shortened_url = create_url(table, url)
    return shortened_url



