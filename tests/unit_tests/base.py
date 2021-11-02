import logging
import unittest

import boto3

from app import app
from app.helpers.urls import create_url
from service_config import AWS_ENDPOINT_URL
from service_config import AWS_REGION
from service_config import AWS_TABLE_NAME

logger = logging.getLogger(__name__)


def create_dynamodb():
    '''Method that creates a mocked DynamoDB for unit testing

    Returns:
        dynamodb: dynamodb resource'''
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION, endpoint_url=AWS_ENDPOINT_URL)
        dynamodb.create_table(
            TableName=AWS_TABLE_NAME,
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
        logger.debug("Table %s already exists but should not.", AWS_TABLE_NAME)
        raise err
    return dynamodb.Table(AWS_TABLE_NAME)


class BaseShortlinkTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=line-too-long
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
