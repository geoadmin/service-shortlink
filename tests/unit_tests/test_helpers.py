import unittest
import logging
import boto3
import unittest
from moto import mock_dynamodb2
import logging.config
from app.helpers import add_item, check_and_get_url_short, create_url, fetch_url
logger = logging.getLogger(__name__)


class TestDynamoDb(unittest.TestCase):

    def setup(self):
        logger.debug("Setting up Dynamo Db tests")
        self.keys_and_urls = {}
        self.testing_urls = []
        self.table = self.create_fake_table()

    @mock_dynamodb2
    def create_fake_table(self):
        logger.debug("Creating fake Dynamo Db Table")
        region = 'eu-central-1'
        dynamodb = boto3.resource('dynamodb', region)

        def populate_table():
            logger.debug("Populating the table using the create_url method")
            for url in self.testing_urls:
                uuid_key = create_url(self.table, url)
                self.keys_and_urls[uuid_key] = url

        table = dynamodb.create_table(
            TableName='shorturl',
            KeySchema=[
                {
                    'AttributeName': 'shortlink_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'url',
                    'KeyType': 'HASH'
                }
            ],
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
                },

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
                        'NonKeyAttributes': ['shortlink_id']
                    }
                },
                {
                    'IndexName': 'shorlinkID',
                    'KeySchema': [
                        {
                            'AttributeName': 'shortlink_id',
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
        populate_table()
        return table

    def test_fetch_url(self):
        for key, url in self.keys_and_urls.items():
            assert (fetch_url(self.table, key) == url)

    def test_check_and_get_url_short(self):
        for key, url in self.keys_and_urls.items():
            assert (check_and_get_url_short(self.table, url) == key)


if __name__ == '__main__':
    unittest.main()
