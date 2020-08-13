import boto3
import flask.exceptions as exc


class DynamodbConnection:
    # We use a singleton approach, as we do not need more than that.
    def __init__(self, region='eu-west-1'):
        self.conn = None
        self.region = region

    def get(self):
        if self.conn is None:
            try:
                self.conn = boto3.resource('dynamodb', region_name=self.region)
            except Exception as e:  # Should be internal error
                raise exc.InternalServerError(
                    'DynamoDB: Error during connection init %s' % e)
        return self.conn


dynamodb_connection = DynamodbConnection()


def get_dynamodb_table(table_name='shorturl', region='eu-west-1'):
    dyn = dynamodb_connection
    dyn.region = region
    conn = dyn.get()
    try:
        table = conn.Table(table_name)
    except Exception as e:  # pragma: no cover
        raise Exception(
            'DynamoDB: Error during connection to the table %s\n%s' % (
                table_name, e))
    return table
