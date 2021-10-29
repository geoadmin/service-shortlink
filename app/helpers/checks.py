import logging
import logging.config
from urllib.parse import urlparse
import re
from service_config import ALLOWED_DOMAINS_PATTERN

from boto3.dynamodb.conditions import Key

from flask import abort

logger = logging.getLogger(__name__)


def check_params(url):
    """
    TODO
    * Quick summary of the function *

    In the process to create a shortened url, this is the first step, checking all parameters. If
    they all fall within expectation, this function return the 'base url' that will lead to the
    redirection link. On production, that base_url would be http(s)://s.geo.admin.ch/.

    * Abortions originating in this function *

    Abort with a 400 status code if there is no url, given to shorten
    Abort with a 400 status code if the url is over 2046 characters long (dynamodb limitation)
    Abort with a 400 status code if the hostname of the URL parameter is not allowed.

    * Abortions originating in functions called from this function *

    None

    * parameters and return values *

    :param url: the url given to be shortened
    """
    if url is None:
        logger.error('No url given to shorten, exiting with a bad request')
        abort(400, 'url parameter missing from request')
        # urls have a maximum size of 2046 character due to a dynamodb limitation
    if len(url) > 2046:
        logger.error("Url(%s) given as parameter exceeds characters limit.", url)
        abort(
            400,
            f"The url given as parameter was too long. (limit is 2046 "
            f"characters, {len(url)} given)"
        )
    if not re.match(ALLOWED_DOMAINS_PATTERN, urlparse(url).hostname):
        logger.error('Hostname %s of the URL parameter is not allowed', urlparse(url).hostname)
        abort(400, 'Host name of the URL parameter is not allowed.')


def check_and_get_shortlinks_id(table, url):
    """
    * Quick summary of the function *

    This tries to fetch the url_id corresponding to the given url in DynamoDB. If the url has
    already been shortened in the past, this will return the shortened url id. Otherwise, it will
    return None

    * Abortions originating in this function *

    None

    * Abortions originating in functions called from this function *

    None

    * Parameters and return values *

    :param table: the dynamodb table on which we execute our query
    :param url: the url we try to compare.
    :return: either a shortened url id, or None
    """
    response = table.query(
        IndexName="UrlIndex",
        KeyConditionExpression=Key('url').eq(url),
    )
    try:
        return response['Items'][0]['shortlinks_id']
    except IndexError:
        logger.debug("The following url ( %s ) was not found in dynamodb", url)
        return None
