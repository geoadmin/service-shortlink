import logging
import re
import unittest

import boto3

from app import app
from app.helpers.urls import create_url
from app.settings import ALLOWED_DOMAINS_PATTERN
from app.settings import AWS_DEFAULT_REGION
from app.settings import AWS_DYNAMODB_TABLE_NAME
from app.settings import AWS_ENDPOINT_URL

logger = logging.getLogger(__name__)


def create_dynamodb():
    '''Method that creates a mocked DynamoDB for unit testing

    Returns:
        dynamodb: dynamodb resource'''
    try:
        dynamodb = boto3.resource(
            'dynamodb', region_name=AWS_DEFAULT_REGION, endpoint_url=AWS_ENDPOINT_URL
        )
        dynamodb.create_table(
            TableName=AWS_DYNAMODB_TABLE_NAME,
            AttributeDefinitions=[
                {
                    'AttributeName': 'url', 'AttributeType': 'S'
                },
                {
                    'AttributeName': 'shortlinks_id', 'AttributeType': 'S'
                },
            ],
            KeySchema=[
                {
                    'AttributeName': 'shortlinks_id', 'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'url', 'KeyType': 'HASH'
                },
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'UrlIndex',
                    'KeySchema': [{
                        'AttributeName': 'url', 'KeyType': 'HASH'
                    }],
                    'Projection': {
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
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 123, 'WriteCapacityUnits': 123
            }
        )
    except dynamodb.meta.client.exceptions.ResourceInUseException as err:
        logger.debug("Table %s already exists but should not.", AWS_DYNAMODB_TABLE_NAME)
        raise err
    return dynamodb.Table(AWS_DYNAMODB_TABLE_NAME)


class BaseShortlinkTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=line-too-long
        cls.context = app.test_request_context()
        cls.context.push()
        cls.app = app.test_client()
        cls.valid_urls_list = [
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.zeitreihen,ch.bfs.gebaeude_wohnungs_register,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=1,1,1,0.8&layers_visibility=false,false,false,false&layers_timestamp=18641231,,,",
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=0.8",
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege,ch.swisstopo.vec200-landcover,ch.bfs.arealstatistik-waldmischungsgrad,ch.bafu.biogeographische_regionen,ch.bfs.arealstatistik-bodenbedeckung-1985&layers_opacity=0.8,0.75,0.75,0.75,0.75&catalogNodes=457,477"
        ]
        cls.invalid_urls_list = [
            "https://map.geo.admin.ch/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/"
        ]
        cls.table = create_dynamodb()
        cls.uuid_to_url_dict = dict()
        for url in cls.valid_urls_list:
            uuid = (create_url(cls.table, url))
            cls.uuid_to_url_dict[uuid] = url
        logger.debug("Setting up Dynamo Db tests")

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()

    def assertCors(self, response, expected_allowed_methods, check_origin=True):  # pylint: disable=invalid-name
        if check_origin:
            self.assertIn('Access-Control-Allow-Origin', response.headers)
            self.assertTrue(
                re.match(ALLOWED_DOMAINS_PATTERN, response.headers['Access-Control-Allow-Origin'])
            )
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertListEqual(
            sorted(expected_allowed_methods),
            sorted(
                map(
                    lambda m: m.strip(),
                    response.headers['Access-Control-Allow-Methods'].split(',')
                )
            )
        )
        self.assertIn('Access-Control-Allow-Headers', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Headers'], '*')

    def assertRedirects(self, response, expected_location, message=None):
        valid_status_codes = (301, 302, 303, 305, 307)
        valid_status_code_str = ', '.join(str(code) for code in valid_status_codes)
        not_redirect = \
            f"HTTP Status {valid_status_code_str} expected but got {response.status_code}"
        self.assertTrue(response.status_code in valid_status_codes, message or not_redirect)
        self.assertEqual(response.location, expected_location, message)
