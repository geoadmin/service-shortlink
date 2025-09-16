import logging
import logging.config
import unittest
from unittest.mock import patch

from werkzeug.exceptions import HTTPException

from app.app import app
from app.helpers.dynamo_db import get_db
from app.helpers.utils import get_url
from tests.unit_tests.base import BaseShortlinkTestCase

logger = logging.getLogger(__name__)


class TestUrlCheck(unittest.TestCase):

    def test_check_params_ok_http(self):
        url_input = 'http://map.geo.admin.ch/enclume'
        with app.test_request_context(json={"url": url_input}):
            try:
                self.assertEqual(url_input, get_url())
            except HTTPException as error:
                self.fail(f'Valid URL raised an exception: {error}')

    def test_check_params_ok_https(self):
        url_input = 'https://map.geo.admin.ch/enclume'
        with app.test_request_context(json={"url": url_input}):
            try:
                self.assertEqual(url_input, get_url())
            except HTTPException as error:
                self.fail(f'Valid URL raised an exception: {error}')

    def test_check_params_no_url(self):
        with app.test_request_context():
            with self.assertRaises(HTTPException) as http_error:
                get_url()
                self.assertEqual(http_error.exception.code, 415)

    def test_check_params_nok_url_empty_string(self):
        with app.test_request_context(data=''):
            with self.assertRaises(HTTPException) as http_error:
                get_url()
                self.assertEqual(http_error.exception.code, 415)

    def test_check_params_non_allowed_url(self):
        input_url = 'https://www.this.is.quite.bad.ch/?layers=ch.bfe.elektromobilität'
        with app.test_request_context(json={'url': input_url}):
            with self.assertRaises(HTTPException) as http_error:
                get_url()
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_invalid_url(self):
        input_url = 'test123'
        with app.test_request_context(json={'url': input_url}):
            with self.assertRaises(HTTPException) as http_error:
                get_url()
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_missing_url(self):
        with app.test_request_context(json={'uri': 'http://www.example.com'}):
            with self.assertRaises(HTTPException) as http_error:
                get_url()
                self.assertEqual(http_error.exception.code, 400)


class TestDynamoDb(BaseShortlinkTestCase):
    """
    Quick note about checker tests parameters :
    In flask request, request.script_root does not consider the prefix to be part of the
    base path, and url_root does not include it either. These are the parameters the function will
    receive.

    """

    def setUp(self):
        super().setUp()
        self.db = get_db()

    def test_fetch_url(self):
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(self.db.get_entry_by_shortlink(uuid)['url'], url)

    def test_fetch_url_nonexistent(self):
        self.assertIsNone(self.db.get_entry_by_shortlink("nonexistent"))

    def test_check_and_get_shortlinks_id(self):
        for uuid, url in self.uuid_to_url_dict.items():
            entry = self.db.get_entry_by_url(url)
            self.assertIsNotNone(entry)
            self.assertEqual(entry['shortlink_id'], uuid)

    def test_check_and_get_shortlinks_id_non_existent(self):
        self.assertEqual(self.db.get_entry_by_url("http://non.existent.url.ch"), None)

    @patch('app.helpers.dynamo_db.generate_short_id')
    def test_duplicate_short_id_max_retry(self, mock_generate_short_id):
        mock_generate_short_id.return_value = '1'
        url1 = 'https://www.example/test-duplicate-id-max-retry-first-url'
        url2 = 'https://www.example/test-duplicate-id-max-retry-second-url'
        entry1 = self.db.add_url_to_table(url1)
        self.assertEqual(entry1['shortlink_id'], '1')
        with self.assertRaises(
            self.db.table.meta.client.exceptions.ConditionalCheckFailedException
        ):
            self.db.add_url_to_table(url2)

    @patch('app.helpers.dynamo_db.generate_short_id')
    def test_one_duplicate_short_id(self, mock_generate_short_id):
        # generare_short_id on the first call return '2', then '2' again and finally '3' in the
        # third call
        mock_generate_short_id.side_effect = ['2', '2', '3']
        url1 = 'https://www.example/test-one-duplicate-id-first-url'
        url2 = 'https://www.example/test-one-duplicate-id-second-url'
        entry1 = self.db.add_url_to_table(url1)
        self.assertEqual(entry1['shortlink_id'], '2')
        entry2 = self.db.add_url_to_table(url2)
        self.assertEqual(entry2['shortlink_id'], '3')
