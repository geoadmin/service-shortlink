import logging
import logging.config
import unittest
import os

import boto3

from moto import mock_dynamodb2
from app import app
from app.helpers.checks import check_and_get_url_short
from app.helpers import add_item
from app.helpers import create_url
from app.helpers import fetch_url

logger = logging.getLogger(__name__)


class TestDynamoDb(unittest.TestCase):

    @mock_dynamodb2
    def setup(self):
        # pylint: disable=attribute-defined-outside-init
        self.valid_urls_list = [
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.zeitreihen,ch.bfs.gebaeude_wohnungs_register,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=1,1,1,0.8&layers_visibility=false,false,false,false&layers_timestamp=18641231,,,",  # pylint: disable=line-too-long
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=0.8",  # pylint: disable=line-too-long
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege,ch.swisstopo.vec200-landcover,ch.bfs.arealstatistik-waldmischungsgrad,ch.bafu.biogeographische_regionen,ch.bfs.arealstatistik-bodenbedeckung-1985&layers_opacity=0.8,0.75,0.75,0.75,0.75&catalogNodes=457,477"  # pylint: disable=line-too-long
        ]
        self.invalid_urls_list = [
            "https://map.geo.admin.ch/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/"  # pylint: disable=line-too-long
        ]
        self.uuid_to_url_dict = dict()
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        logger.debug("Setting up Dynamo Db tests")
        region = 'eu-central-1'
        self.connection = boto3.resource('dynamodb', region)
        logger.warning("Right before table creation")
        self.connection.create_table(
            TableName='shorturl',
            AttributeDefinitions=[
                    {
                        'AttributeName': 'url',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'url_short',
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
                    }
            ],
            LocalSecondaryIndexes=[
                    {
                        'IndexName': 'UrlIndex',
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
                        'IndexName': 'shortlinkID',
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
        self.table = self.connection.Table('shorturl')
        for url in self.valid_urls_list:
            uuid = (create_url(self.table, url))
            self.uuid_to_url_dict[uuid] = url

    @mock_dynamodb2
    def test_fetch_url(self):
        self.setup()
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(fetch_url(self.table, uuid, "test.admin.ch/"), url)

    @mock_dynamodb2
    def test_fetch_url_nonexistent(self):
        self.setup()
        with app.app_context() as context:
            self.assertEqual(fetch_url(self.table, "nonexistent", "test.admin.ch/"), "")

    @mock_dynamodb2
    def test_check_and_get_url_short(self):
        self.setup()
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(check_and_get_url_short(self.table, url), uuid)

    @mock_dynamodb2
    def test_check_and_get_url_short_non_existent(self):
        self.setup()
        self.assertEqual(check_and_get_url_short(self.table, "http://non.existent.url.ch"), None)

    @mock_dynamodb2
    def test_add_item(self):
        self.setup()
        self.assertEqual(self.table.item_count, len(self.valid_urls_list))
        for url in self.uuid_to_url_dict.values():
            add_item(self.table, url)
        self.assertEqual(self.table.item_count, len(self.valid_urls_list))
        add_item(self.table, "http://map.geo.admin.ch")
        self.assertEqual(self.table.item_count, len(self.valid_urls_list) + 1)


if __name__ == '__main__':
    unittest.main()
