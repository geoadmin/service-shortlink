import logging
import logging.config
import boto3
import boto3.exceptions as boto3_exc
from flask import abort
from app import app
from app.helpers.response_generation import make_error_msg
config = app.config
logger = logging.getLogger(__name__)


class DynamodbConnection:
    # We use a singleton approach, as we do not need more than that.
    def __init__(self, region='eu-central-1'):
        self.conn = None
        self.region = region

    def get(self):
        if self.conn is None:
            try:
                self.conn = boto3.resource('dynamodb', region_name=self.region)
            except boto3_exc.Boto3Error as error:
                logger.error(
                    'internal error during Dynamodb connection init. message is : {error}'.format(
                        error=str(error)
                    )
                )
                abort(make_error_msg(500, 'Internal error'))
        return self.conn


dynamodb_connection = DynamodbConnection()


def get_dynamodb_table():
    table_name = config.get('aws_table_name', 'shorturl')
    region = config.get('aws_region', 'eu-central-1')
    dyn = dynamodb_connection
    dyn.region = region
    conn = dyn.get()
    try:
        return conn.Table(table_name)
    except boto3_exc.Boto3Error as error:
        logger.error(
            'DynamoDB error during connection to the table {table}. Error message is {error}'.
            format(table=table_name, error=str(error))
        )
        abort(make_error_msg(500, 'Internal error'))
