import time
import logging
import logging.config
import os
import uuid
import yaml
import boto3.exceptions as boto3_exc
from boto3.dynamodb.conditions import Key
from flask import abort

from app.helpers.checks import check_and_get_url_short
from app.helpers.response_generation import make_error_msg
from app import app
config = app.config
logger = logging.getLogger(__name__)


def create_url(table, url):
    """
    * Quick summary of the function *

    This function creates an id using a magic number based on epoch, then try to write to DynamoDB
    to save the short url.

    * abortions originating in this function *

    abort with a 500 status code on a writing error in DynamoDB

    * abortions originating in functions called from this function *

    None

    raise Exceptions when there is an issue during the dynamo db table write
    * parameters and expected output *

    :param table: the aws table on which we will write
    :param url: the url we want to shorten
    :return: the shortened url id
    """
    logger.debug("Entry in create_url function")
    logger.debug(table)
    try:
        # we create a magic number based on epoch for our shortened_url id
        # shortened_url = uuid.uuid5(uuid.NAMESPACE_URL, url).hex
        shortened_url = f'{int(time.time() * 1000) - 1000000000000}'
        now = time.localtime()
        table.put_item(
            Item={
                'url_short': shortened_url,
                'url': url,
                'timestamp': time.strftime('%Y-%m-%d %X', now),
                'epoch': str(time.gmtime())
            }
        )
        logger.info(
            "Exit create_url function with shortened url --> %s", shortened_url
        )
        return shortened_url
    # Those are internal server error: error code 500
    except boto3_exc.Boto3Error as error:
        logger.error(
            "Internal error while writing in dynamodb. Error message is %s", str(error)
        )
        abort(make_error_msg(500, f"Write units exceeded: {str(error)}"))


def fetch_url(table, url_id, url_root):
    """
    * Quick summary of the function *

    We try to look for the url_id in the dynamodb table to find the corresponding full url

    * abortions originating in this function *

    abort with a 500 status code on a read error
    abort with a 404 status code if the url_id is not an index for a shortened url

    * abortions originating in functions called from this function *

    abort with 500 error from get_dynamodb_table

    * parameters and expected output *

    :param table: DynamoDb Table object
    :param url_id: String, a shortened url to be compared against indexes in DynamoDB
    :param url_root: String, the base url of the service. For example, in dev, it would be
    https://service-shortlink.dev.bgdi.ch/
    :return url: the full url corresponding to the url_id in DynamoDB
    """

    url = None

    try:
        response = table.query(
            IndexName='shortlinkID', KeyConditionExpression=Key('url_short').eq(url_id)
        )
        url = response['Items'][0]['url'] if len(response['Items']) > 0 else None

    except boto3_exc.Boto3Error as error:  # pragma: no cover
        logger.error(
            "Internal Error while reading in dynamodb. Error message is %s", str(error)
        )
        abort(make_error_msg(500, f'Unexpected internal server error: {str(error)}'))
    if url is None:
        logger.error("The Shortlink %s was not found in dynamodb.", url_id)
        abort(make_error_msg(404, f'This short url doesn\'t exist: {url_root}{str(url_id)}'))
    return url


def add_item(table, url):
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

    :param table: DynamoDb Table object
    :param url: the url we want to shorten
    :return: the shortened url id
    """
    shortened_url = check_and_get_url_short(table, url)
    if shortened_url is None:
        shortened_url = create_url(table, url)
    return shortened_url


def get_logging_cfg():
    cfg_file = os.getenv('LOGGING_CFG', 'logging-cfg-local.yml')

    with open(cfg_file, 'rt') as fd:
        cfg = yaml.safe_load(fd.read())
        fd.close()
        logger.debug('Load logging configuration from file %s', cfg_file)
        return cfg


def init_logging():
    cfg = get_logging_cfg()
    logging.config.dictConfig(cfg)
