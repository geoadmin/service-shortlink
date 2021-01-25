import logging
import logging.config
import unittest
import os

import boto3

from moto import mock_dynamodb2
from werkzeug.exceptions import HTTPException

from app import app
from app.helpers.checks import check_params
from app.helpers.checks import check_and_get_shortlinks_id
from app.helpers.urls import add_item
from app.helpers.urls import create_url
from app.helpers.urls import fetch_url
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
            TableName='shortlinks_test',
            AttributeDefinitions=[
                {
                    'AttributeName': 'url', 'AttributeType': 'S'
                }, {
                    'AttributeName': 'shortlinks_id', 'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'shortlinks_id', 'KeyType': 'HASH'
                }, {
                    'AttributeName': 'url', 'KeyType': 'HASH'
                }
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'UrlIndex',
                    'KeySchema': [{
                        'AttributeName': 'url', 'KeyType': 'HASH'
                    }],
                    'Projection':
                        {
                            'ProjectionType': 'INCLUDE', 'NonKeyAttributes': ['shortlinks_id']
                        }
                },
                {
                    'IndexName': 'ShortlinksIndex',
                    'KeySchema': [{
                        'AttributeName': 'shortlinks_id', 'KeyType': 'HASH'
                    }],
                    'Projection': {
                        'ProjectionType': 'INCLUDE', 'NonKeyAttributes': ['url']
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 123, 'WriteCapacityUnits': 123
            }
        )
        self.table = self.connection.Table('shortlinks_test')
        for url in self.valid_urls_list:
            uuid = (create_url(self.table, url))
            self.uuid_to_url_dict[uuid] = url

    def test_check_params_ok_http(self):
        with app.app_context():
            base_path = check_params(
                scheme='http',
                host='api3.geo.admin.ch',
                url='https://map.geo.admin.ch/enclume',
                base_path='/v4/shortlink'
            )
            self.assertEqual(base_path, 'http://s.geo.admin.ch/')

    def test_check_params_ok_https(self):
        with app.app_context():
            base_path = check_params(
                scheme='https',
                host='api3.geo.admin.ch',
                url='https://map.geo.admin.ch/enclume',
                base_path='/v4/shortlink'
            )
            self.assertEqual(base_path, 'https://s.geo.admin.ch/')

    def test_check_params_ok_non_standard_host(self):
        with app.app_context():
            base_path = check_params(
                scheme='https',
                host='service-shortlink.dev.bgdi.ch',
                url='https://map.geo.admin.ch/enclume',
                base_path='/v4/shortlink'
            )
            self.assertEqual(
                base_path, 'https://service-shortlink.dev.bgdi.ch/v4/shortlink/shortlinks/'
            )

    def test_check_params_nok_no_url(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(
                    scheme='https',
                    host='service-shortlink.dev.bgdi.ch',
                    url=None,
                    base_path='/v4/shortlink'
                )
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_nok_url_empty_string(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(
                    scheme='https',
                    host='service-shortlink.dev.bgdi.ch',
                    url='',
                    base_path='/v4/shortlink'
                )
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_nok_url_no_host(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(
                    scheme='https',
                    host='service-shortlink.dev.bgdi.ch',
                    url='/?layers=ch.bfe.elektromobilität',
                    base_path='/v4/shortlink'
                )
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_nok_url_from_non_valid_domains_or_hostname(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(
                    scheme='https',
                    host='service-shortlink.dev.bgdi.ch',
                    url='https://www.this.is.quite.invalid.ch/?layers=ch.bfe.elektromobilität',
                    base_path='/v4/shortlink'
                )
                self.assertEqual(http_error.exception.code, 400)

    @mock_dynamodb2
    def test_fetch_url(self):
        self.setup()
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(fetch_url(self.table, uuid, "test.admin.ch/"), url)

    @mock_dynamodb2
    def test_fetch_url_nonexistent(self):
        self.setup()
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                fetch_url(self.table, "nonexistent", "test.admin.ch/")
                self.assertEqual(http_error.exception.code, 400)

    @mock_dynamodb2
    def test_check_and_get_shortlinks_id(self):
        self.setup()
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(check_and_get_shortlinks_id(self.table, url), uuid)

    @mock_dynamodb2
    def test_check_and_get_shortlinks_id_non_existent(self):
        self.setup()
        self.assertEqual(
            check_and_get_shortlinks_id(self.table, "http://non.existent.url.ch"), None
        )

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
