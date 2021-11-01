import logging
import logging.config
import os
import unittest

import boto3
from moto import mock_dynamodb2
from werkzeug.exceptions import HTTPException

from app import app
from app.helpers.checks import check_and_get_shortlinks_id
from app.helpers.checks import check_params
from app.helpers.urls import add_item
from app.helpers.urls import create_url
from app.helpers.urls import fetch_url

logger = logging.getLogger(__name__)


class BaseTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # pylint: disable=attribute-defined-outside-init
        cls.valid_urls_list = [
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.zeitreihen,ch.bfs.gebaeude_wohnungs_register,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=1,1,1,0.8&layers_visibility=false,false,false,false&layers_timestamp=18641231,,,",  # pylint: disable=line-too-long
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=0.8",  # pylint: disable=line-too-long
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege,ch.swisstopo.vec200-landcover,ch.bfs.arealstatistik-waldmischungsgrad,ch.bafu.biogeographische_regionen,ch.bfs.arealstatistik-bodenbedeckung-1985&layers_opacity=0.8,0.75,0.75,0.75,0.75&catalogNodes=457,477"  # pylint: disable=line-too-long
        ]
        cls.invalid_urls_list = [
            "https://map.geo.admin.ch/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/"  # pylint: disable=line-too-long
        ]
        cls.uuid_to_url_dict = dict()
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        logger.debug("Setting up Dynamo Db tests")
        region = 'eu-central-1'
        cls.connection = boto3.resource('dynamodb', region)
        logger.warning("Right before table creation")
        cls.connection.create_table(
            TableName='shortlinks_test',
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
        cls.table = cls.connection.Table('shortlinks_test')
        for url in cls.valid_urls_list:
            uuid = (create_url(cls.table, url))
            cls.uuid_to_url_dict[uuid] = url
