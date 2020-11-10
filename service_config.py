import os
import re


class Config(object):
    """
    The Config class contains everything needed to run the service. Most entries have a default
    value and an environment value to override it.

    """
    allowed_domains = os.environ.get('ALLOWED_DOMAINS', 'admin.ch,swisstopo.ch,bgdi.ch').split(',')
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', 'api.geo.admin.ch,api3.geo.admin.ch').split(',')
    aws_table_name = os.environ.get('AWS_DYNAMODB_TABLE_NAME', 'shortlink')
    aws_region = os.environ.get('AWS_DYNAMODB_TABLE_REGION', 'eu-west-1')
    allowed_domains_pattern = re.compile("^.*\.admin\.ch|.*\.swisstopo\.cloud|.*\.bgdi\.ch$")
