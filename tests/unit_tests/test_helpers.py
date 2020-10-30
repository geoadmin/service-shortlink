import unittest
import logging
import boto3
import unittest
import os
import time
from moto import mock_dynamodb2
import logging.config
logger = logging.getLogger(__name__)


class TestDynamoDb(unittest.TestCase):
    @mock_dynamodb2
    def setup(self):
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        logger.debug("Setting up Dynamo Db tests")
        region = 'eu-central-1'
        self.connection = boto3.resource('dynamodb', region)
        # self.conn = boto3.resource('dynamodb', region_name=self.region)
        self.keys_and_urls = {}
        self.testing_urls = ["https://map.geo.admin"]
        self.create_fake_table(self.connection)
        self.table = self.connection.Table('shorturl')
        logger.info(self.table)
        self.populate_table()

    @mock_dynamodb2
    def populate_table(self):
        from app.helpers import create_url
        logger.warning("Populating the table using the create_url method")
        logger.info(self.testing_urls)

        for url in self.testing_urls:
            logger.info(url)
            logger.info(self.table)
            """uuid_key = "10341324ef"
            now = time.localtime()
            self.table.put_item(
                Item={
                    'url_short': uuid_key,
                    'url': url,
                    'timestamp': time.strftime('%Y-%m-%d %X', now),
                    'epoch': str(time.gmtime())
                })"""
            uuid_key = create_url(self.table, url)
            self.keys_and_urls[uuid_key] = url
        logger.warning(self.keys_and_urls)

    @mock_dynamodb2
    def create_fake_table(self, connection):

        logger.warning("Right before table creation")
        connection.create_table(
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

    def test_fetch_url(self):
        from app.helpers import fetch_url
        logger.warning("in test_fetch_url")
        self.setup()
        for key, url in self.keys_and_urls.items():
            assert (fetch_url(self.table, key) == url)

    def test_check_and_get_url_short(self):
        from app.helpers import check_and_get_url_short
        self.setup()
        for key, url in self.keys_and_urls.items():
            assert (check_and_get_url_short(self.table, url) == key)


if __name__ == '__main__':
    unittest.main()
