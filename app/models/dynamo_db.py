import boto3
from flask import abort
from app.helpers.response_generation import make_error_msg


class DynamodbConnection:
    # We use a singleton approach, as we do not need more than that.
    def __init__(self, region='eu-west-1'):
        self.conn = None
        self.region = region

    def get(self):
        if self.conn is None:
            try:
                self.conn = boto3.resource('dynamodb', region_name=self.region)
            except Exception as e:
                abort(make_error_msg(500, f'DynamoDB: Error during connection init {e}'))
        return self.conn


dynamodb_connection = DynamodbConnection()


def get_dynamodb_table(table_name='shorturl', region='eu-west-1'):
    dyn = dynamodb_connection
    dyn.region = region
    conn = dyn.get()
    try:
        table = conn.Table(table_name)
    except Exception as e:  # pragma: no cover
        abort(make_error_msg(500, f'DynamoDB: Error during connection to the table {table_name}\n{e}'))
    return table
