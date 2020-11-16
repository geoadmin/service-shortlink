import json
import logging
import logging.config
import re
import os
import unittest

import boto3

from flask_testing import TestCase
from moto import mock_dynamodb2
from mock import patch


from app import app
from app.helpers import create_url
import service_config

app.config['allowed_hosts'] = service_config.Config.allowed_hosts
app.config['allowed_domains'] = service_config.Config.allowed_domains

logger = logging.getLogger(__name__)


class TestRoutes(unittest.TestCase):

    @mock_dynamodb2
    def setUp(self):
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=line-too-long
        self.app = app.test_client()
        self.valid_urls_list = [
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.zeitreihen,ch.bfs.gebaeude_wohnungs_register,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=1,1,1,0.8&layers_visibility=false,false,false,false&layers_timestamp=18641231,,,",
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=0.8",
            "https://map.geo.admin.ch/?lang=fr&topic=ech&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.swisstopo.swisstlm3d-wanderwege,ch.swisstopo.vec200-landcover,ch.bfs.arealstatistik-waldmischungsgrad,ch.bafu.biogeographische_regionen,ch.bfs.arealstatistik-bodenbedeckung-1985&layers_opacity=0.8,0.75,0.75,0.75,0.75&catalogNodes=457,477"
        ]
        self.invalid_urls_list = [
            "https://map.geo.admin.ch/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/"
        ]
        self.uuid_to_url_dict = dict()
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        logger.debug("Setting up Dynamo Db tests")
        region = 'eu-central-1'
        self.connection = boto3.resource('dynamodb', region)
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

    def __fake_get_dynamo_db(self):
        return self.table

    def test_checker_ok(self):
        # checker
        self.setUp()
        response = self.app.get(
            "/checker", headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json, {'success': True, 'message': 'OK'})

    @mock_dynamodb2
    def test_create_shortlink_ok(self):
        self.setUp()
        import app.models.dynamo_db as dynamo_db
        with patch.object(dynamo_db, 'get_dynamodb_table', return_value=self.__fake_get_dynamo_db()):
            response = self.app.post(
                "/shorten",
                data=json.dumps({"url": "https://map.geo.admin.ch/test"}),
                content_type="application/json",
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertEqual(response.json.get('success'), True)
            shorturl = response.json.get('shorturl')
            self.assertEqual('http://localhost/redirect/' in shorturl, True)
            shorturl = shorturl.replace('http://localhost/redirect/', '')
            self.assertEqual(re.search(r"^\d{12}$", shorturl) is not None, True)

    """
    The following tests should all return a 400 error code
    """
    def test_create_shortlink_no_json(self):
        self.setUp()
        response = self.app.post(
            "/shorten",
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual("application/json", response.content_type)
        self.assertEqual({
            'success': False,
            'error': {
                'code': 400,
                'message': 'This service requires a json to be posted as a payload.'
            }
        }, response.json)

    def test_create_shortlink_no_url(self):
        self.setUp()
        response = self.app.post(
            "/shorten",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual("application/json", response.content_type)
        self.assertEqual({
            'success': False,
            'error': {
                'code': 400,
                'message': 'url parameter missing from request'
            }

            }, response.json)

    def test_create_shortlink_no_hostname(self):
        self.setUp()
        response = self.app.post(
            "/shorten",
            data=json.dumps({"url": "/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {
            'success': False,
            'error': {
                'code': 400,
                'message': 'Could not determine the query hostname'
            }
        })

    def test_create_shortlink_non_allowed_hostname_and_domain(self):
        self.setUp()
        response = self.app.post(
            "/shorten",
            data=json.dumps({"url": "https://not.a.valid.hostname.ch/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {
            'success': False,
            'error': {
                'code': 400,
                'message': 'Neither Host nor Domain in the url parameter are valid'
            }
        })

    def test_create_shortlink_url_too_long(self):
        self.setUp()
        url = "https://map.geo.admin.ch/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/" # pylint: disable=line-too-long
        response = self.app.post(
            "/shorten",
            data=json.dumps({"url": url}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {
            'success': False,
            'error': {
                'code': 400,
                'message': "The url given as parameter was too long. "
                           "(limit is 2046 characters, 2946 given)"
            }
        })

    @mock_dynamodb2
    def test_redirect_shortlink_ok(self):
        self.setUp()
        import app.models.dynamo_db as dynamo_db
        with patch.object(dynamo_db, 'get_dynamodb_table', return_value=self.__fake_get_dynamo_db()):
            for shortid, url in self.uuid_to_url_dict.items():
                response = self.app.get(
                    f"/redirect/{shortid}",
                    content_type="text/html",
                    headers={"Origin": "map.geo.admin.ch"}
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.content_type, "text/html; charset=utf-8")
                TestCase().assertRedirects(response, url)

    # The following test will return a 404
    @mock_dynamodb2
    def test_redirect_shortlink_url_not_found(self):
        self.setUp()
        import app.models.dynamo_db as dynamo_db
        with patch.object(dynamo_db, 'get_dynamodb_table', return_value=self.__fake_get_dynamo_db()):
            response = self.app.get(
                "/redirect/nonexistent",
                content_type="text/html; charset=utf-8",
                headers={"Origin": "map.geo.admin.ch"}
            )
            expected_json = {
                'success': False,
                'error': {
                    'code': 404,
                    'message': "This short url doesn't exist: http://localhost/nonexistent"
                }
            }
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content_type, "application/json")
            self.assertEqual(response.json, expected_json)

    @mock_dynamodb2
    def test_fetch_full_url_from_shortlink_ok(self):
        self.setUp()
        import app.models.dynamo_db as dynamo_db
        with patch.object(dynamo_db, 'get_dynamodb_table', return_value=self.__fake_get_dynamo_db()):
            for shortid, url in self.uuid_to_url_dict.items():
                response = self.app.get(
                    f"/{shortid}",
                    content_type="application/json",
                    headers={"Origin": "map.geo.admin.ch"}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content_type, "application/json; charset=utf-8")
                self.assertEqual(response.json, {
                    'shorturl': shortid,
                    'full_url': url,
                    'success': True
                })

    @mock_dynamodb2
    def test_fetch_full_url_from_shortlink_url_not_found(self):
        self.setUp()
        import app.models.dynamo_db as dynamo_db
        with patch.object(dynamo_db, 'get_dynamodb_table', return_value=self.__fake_get_dynamo_db()):
            response = self.app.get(
                "/nonexistent",
                content_type="application/json",
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content_type, "application/json")
            expected_json = {
                'error': {
                    'code': 404,
                    'message': "This short url doesn't exist: http://localhost/nonexistent"
                },
                'success': False
            }
            self.assertEqual(response.json, expected_json)


if __name__ == '__main__':
    unittest.main()
