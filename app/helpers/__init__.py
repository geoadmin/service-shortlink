import time
import logging
import uuid
import boto3.exceptions as boto3_exc
from boto3.dynamodb.conditions import Key
from flask import abort

from app.helpers.checks import check_and_get_url_short
from app.helpers.response_generation import make_error_msg
from app.models.dynamo_db import get_dynamodb_table
from app import app
config = app.config
logger = logging.getLogger(__name__)


def create_url(table, url):
    """
    * Quick summary of the function *

    This function creates an id using the uuid library which will act as the shortened url,
    store it in DynamoDB and returns it

    * abortions originating in this function *

    abort with a 400 status code if the url given as parameter exceeds 2046 characters (DynamoDB
    limitation)
    abort with a 500 status code on a writing error in DynamoDB

    * abortions originating in functions called from this function *

    None

    raise Exceptions when there is an issue during the dynamo db table write
    * parameters and expected output *

    :param table: the aws table on which we will write
    :param url: the url we want to shorten
    :return: the shortened url id
    """
    logger.info("Entry in create_url function")
    logger.debug(f"Parameters for the function : table --> {table.__repr__}, url --> {url}")
    try:
        # we create a magic number based on epoch for our shortened_url id
        # urls have a maximum size of 2046 character due to a dynamodb limitation
        if len(url) > 2046:
            logger.error(f"Url({url}) given as parameter exceeds characters limit.")
            abort(make_error_msg(400, f"The url given as parameter was too long. (limit is 2046 "
                                      f"characters, {len(url)} given)"))
        shortened_url = uuid.uuid5(uuid.NAMESPACE_URL, url).hex
        now = time.localtime()
        table.put_item(
            Item={
                'url_short': shortened_url,
                'url': url,
                'timestamp': time.strftime('%Y-%m-%d %X', now),
                'epoch': time.strftime('%s', now)
            }
        )
        logger.info(f"Exit create_url function with shortened url --> {shortened_url}")
        return shortened_url
    # Those are internal server error: error code 500
    except boto3_exc.Boto3Error as e:
        logger.error(f"Internal error while writing in dynamodb. Error message is {str(e)}")
        abort(make_error_msg(500, f"Write units exceeded: {str(e)}"))


def fetch_url(url_id):
    """
    * Quick summary of the function *

    We try to look for the url_id in the dynamodb table to find the corresponding full url

    * abortions originating in this function *

    abort with a 500 status code on a read error
    abort with a 404 status code if the url_id is not an index for a shortened url

    * abortions originating in functions called from this function *

    abort with 500 error from get_dynamodb_table

    * parameters and expected output *

    :param url_id: String, a shortened url to be compared against indexes in DynamoDB
    :return url: the full url corresponding to the url_id in DynamoDB
    """
    url_short = url_id

    table_name = config['aws_table_name']
    aws_region = config['aws_region']
    url = None
    table = get_dynamodb_table(table_name=table_name, region=aws_region)

    try:
        response = table.query(
            KeyConditionExpression=Key('url_short').eq(url_short)
        )
        url = response['Items'][0]['url'] if len(response['Items']) > 0 else None

    except boto3_exc.Boto3Error as e:  # pragma: no cover
        abort(make_error_msg(500, f'Unexpected internal server error: {str(e)}'))
    if url is None:
        abort(make_error_msg(404, f'This short url doesn\'t exist: s.geo.admin.ch/{str(url_id)}'))
    return url


def add_item(url):
    """
    * Quick summary of the function *

    This function set a connection to a table, checks if the shortened url exists, creates it if
    that is not the case and returns the shortened url

    * abortions originating in this function *

    None

    * abortions originating in functions called from this function *

    Abort with a 400 status code from create_url
    Abort with a 500 status code from get_dynamodb_table or create_url

    * parameters and expected output *

    :param url: the url we want to shorten
    :return: the shortened url id
    """
    table = get_dynamodb_table(config['aws_table_name'], config['aws_region'])
    shortened_url = check_and_get_url_short(table, url)
    if shortened_url is None:
        shortened_url = create_url(table, url)
    return shortened_url



