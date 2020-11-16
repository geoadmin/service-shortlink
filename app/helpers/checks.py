import logging
import logging.config
from urllib.parse import urlparse

from boto3.dynamodb.conditions import Key
from flask import abort

from app.helpers.response_generation import make_error_msg
from app import app

config = app.config
logger = logging.getLogger(__name__)


def check_params(scheme, host, url, base_path):
    """
    * Quick summary of the function *

    In the process to create a shortened url, this is the first step, checking all parameters. If
    they all fall within expectation, this function return the 'base url' that will lead to the
    redirection link. On production, that base_url would be http(s)://s.geo.admin.ch/.

    * Abortions originating in this function *

    Abort with a 400 status code if there is no url, given to shorten
    Abort with a 400 status code if the url is over 2046 characters long (dynamodb limitation)
    Abort with a 400 status code if the application hostname can't be determined
    Abort with a 400 status code if the application domain is not one of the allowed ones.

    * Abortions originating in functions called from this function *

    None

    * parameters and return values *

    :param scheme: the scheme (http | https) used to make the query
    :param host: the hostname of this service
    :param url: the url given to be shortened
    :param base_path: the reverse proxy paths in front of this service
    :return: the base url to reach the redirected url.
    """
    if url is None:
        logger.error('No url given to shorten, exiting with a bad request')
        abort(make_error_msg(400, 'url parameter missing from request'))
        # urls have a maximum size of 2046 character due to a dynamodb limitation
    if len(url) > 2046:
        logger.error("Url(%s) given as parameter exceeds characters limit.", url)
        abort(
            make_error_msg(
                400,
                f"The url given as parameter was too long. (limit is 2046 "
                f"characters, {len(url)} given)"
            )
        )
    hostname = urlparse(url).hostname
    if hostname is None:
        logger.error("Could not determine hostname from the following url : %s", url)
        abort(make_error_msg(400, 'Could not determine the query hostname'))
    domain = ".".join(hostname.split(".")[-2:])
    if domain not in config['allowed_domains'] and hostname not in config['allowed_hosts']:
        logger.error(
            "neither the hostname (%s) nor the domain(%s) are part of their "
            "respective allowed list of domains (%s) or "
            "hostnames(%s)",
            hostname,
            domain,
            ', '.join(config['allowed_domains']),
            ', '.join(config['allowed_hosts'])
        )
        abort(make_error_msg(400, 'Neither Host nor Domain in the url parameter are valid'))
    if host not in config['allowed_hosts']:
        """
        This allows for compatibility with dev hosts or local builds for testing purpose.
        """
        host = host.replace('://', '')  # We make sure here that the :// can't get duplicated in the shorturl
        base_url = ''.join(
            (scheme, '://', host, base_path if 'localhost' not in host else '', 'redirect/')
        )
    else:
        base_url = ''.join((scheme, '://s.geo.admin.ch/'))

    return base_url


def check_and_get_url_short(table, url):
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
        return response['Items'][0]['url_short']
    except IndexError:
        return None
