import logging
import logging.config

import boto3
import boto3.exceptions as boto3_exc

from app.settings import AWS_ENDPOINT_URL
from app.settings import AWS_REGION
from app.settings import AWS_TABLE_NAME

logger = logging.getLogger(__name__)


class DynamodbConnection:
    # We use a singleton approach, as we do not need more than that.
    def __init__(self, region='eu-central-1', endpoint=AWS_ENDPOINT_URL):
        self.conn = None
        self.region = region
        self.endpoint = endpoint

    def get(self):
        if self.conn is None:
            try:
                self.conn = boto3.resource(
                    'dynamodb', region_name=self.region, endpoint_url=self.endpoint
                )
            except boto3_exc.Boto3Error as error:
                logger.error(
                    'internal error during Dynamodb connection init. message is : %s', str(error)
                )
                raise
        return self.conn


dynamodb_connection = DynamodbConnection()


def get_dynamodb_table():
    table_name = AWS_TABLE_NAME
    region = AWS_REGION
    dyn = dynamodb_connection
    dyn.region = region
    dyn.endpoint = AWS_ENDPOINT_URL
    conn = dyn.get()
    try:
        return conn.Table(table_name)
    except boto3_exc.Boto3Error as error:
        logger.error(
            'DynamoDB error during connection to the table %s. Error message is %s',
            table_name,
            str(error)
        )
        raise
