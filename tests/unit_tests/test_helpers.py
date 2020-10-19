import unittest
import logging
import boto3
import unittest
from moto import mock_dynamodb2, mock_iam
import logging.config
from app.helpers import add_item, check_and_get_url_short, create_url, fetch_url
logger = logging.getLogger(__name__)


class TestDynamoDb(unittest.TestCase):
    def setup(self):
        logger.debug("Setting up Dynamo Db tests")
        self.keys_and_urls = {}
        self.testing_urls = ["https://map.geo.admin"]
        self.table = self.create_fake_table()
        self.populate_table()

    def populate_table(self):
        logger.warning("Populating the table using the create_url method")
        for url in self.testing_urls:
            uuid_key = create_url(self.table, url)
            self.keys_and_urls[uuid_key] = url
        logger.warning(self.keys_and_urls)

    @mock_dynamodb2
    def create_fake_table(self):
        region = 'eu-central-1'
        dynamodb = boto3.resource('dynamodb', region)

        logger.warning("Right before table creation")
        table = dynamodb.create_table(
            TableName='shorturl',
            AttributeDefinitions=[
                {
                    'AttributeName': 'url',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'url_short',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'epoch',
                    'AttributeType': 'S'
                }

            ],

            KeySchema=[
                {
                    'AttributeName': 'url_short',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'url',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'epoch',
                    'KeyType': 'HASH'
                }
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'URL',
                    'KeySchema': [
                        {
                            'AttributeName': 'url',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'INCLUDE',
                        'NonKeyAttributes': ['url_short']
                    }
                },
                {
                    'IndexName': 'shorlinkID',
                    'KeySchema': [
                        {
                            'AttributeName': 'url_short',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'INCLUDE',
                        'NonKeyAttributes': ['url']
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 123,
                'WriteCapacityUnits': 123
            }
        )
        return table

    def test_fetch_url(self):
        logger.warning("in test_fetch_url")
        self.setup()
        for key, url in self.keys_and_urls.items():
            assert (fetch_url(self.table, key) == url)

    def test_check_and_get_url_short(self):
        self.setup()
        for key, url in self.keys_and_urls.items():
            assert (check_and_get_url_short(self.table, url) == key)


if __name__ == '__main__':
    with mock_iam():
        boto3.setup_default_session()
        iam_resource = boto3.resource('iam')
        user = iam_resource.create_user(UserName='john') # succeeds
        print(user)
        unittest.main()
