import logging
import logging.config
import unittest

from werkzeug.exceptions import HTTPException

from app import app
from app.helpers.checks import check_and_get_shortlinks_id
from app.helpers.checks import check_params
from app.helpers.urls import add_item
from app.helpers.urls import fetch_url
from tests.unit_tests.base import BaseShortlinkTestCase

logger = logging.getLogger(__name__)


def test_check_params_ok_http(self):
    with app.app_context():
        check_params(url='http://map.geo.admin.ch/enclume')


def test_check_params_ok_https(self):
    with app.app_context():
        check_params(url='https://map.geo.admin.ch/enclume')


class TestDynamoDb(BaseShortlinkTestCase):
    """
    Quick note about checker tests parameters :
    In flask request, request.script_root does not consider the prefix to be part of the
    base path, and url_root does not include it either. These are the parameters the function will
    receive.

    """

    def test_check_params_no_url(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(url=None)
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_nok_url_empty_string(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(url='')
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_non_allowed_url(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(
                    url='https://www.this.is.quite.bad.ch/?layers=ch.bfe.elektromobilität',
                )
                self.assertEqual(http_error.exception.code, 400)

    def test_check_params_invalid_url(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                check_params(url='test123',)
                self.assertEqual(http_error.exception.code, 400)

    def test_fetch_url(self):
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(fetch_url(self.table, uuid, "test.admin.ch/"), url)

    def test_fetch_url_nonexistent(self):
        with app.app_context():
            with self.assertRaises(HTTPException) as http_error:
                fetch_url(self.table, "nonexistent", "test.admin.ch/")
                self.assertEqual(http_error.exception.code, 400)

    def test_check_and_get_shortlinks_id(self):
        for uuid, url in self.uuid_to_url_dict.items():
            self.assertEqual(check_and_get_shortlinks_id(self.table, url), uuid)

    def test_check_and_get_shortlinks_id_non_existent(self):
        self.assertEqual(
            check_and_get_shortlinks_id(self.table, "http://non.existent.url.ch"), None
        )

    def test_add_item(self):
        self.assertEqual(self.table.item_count, len(self.valid_urls_list))
        for url in self.uuid_to_url_dict.values():
            add_item(self.table, url)
        self.assertEqual(self.table.item_count, len(self.valid_urls_list))
        add_item(self.table, "http://map.geo.admin.ch")
        self.assertEqual(self.table.item_count, len(self.valid_urls_list) + 1)


if __name__ == '__main__':
    unittest.main()
