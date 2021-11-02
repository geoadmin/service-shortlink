import json
import logging
import logging.config
import re
import unittest

from flask_testing import TestCase

from tests.unit_tests.base import BaseShortlinkTestCase

logger = logging.getLogger(__name__)


class TestRoutes(BaseShortlinkTestCase):

    def test_checker_ok(self):
        # checker
        response = self.app.get("/checker", headers={"Origin": "map.geo.admin.ch"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json, {'success': True, 'message': 'OK'})

    def test_create_shortlink_ok(self):
        response = self.app.post(
            "/",
            data=json.dumps({"url": "https://map.geo.admin.ch/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json.get('success'), True)
        shorturl = response.json.get('shorturl')
        self.assertEqual('http://localhost/' in shorturl, True)
        shorturl = shorturl.replace('http://localhost/', '')
        self.assertEqual(re.search(r"^\d{12}$", shorturl) is not None, True)

    """
    The following tests should all return a 400 error code
    """

    def test_create_shortlink_no_json(self):
        response = self.app.post("/", headers={"Origin": "map.geo.admin.ch"})
        self.assertEqual(400, response.status_code)
        self.assertEqual("application/json", response.content_type)
        self.assertEqual({
            'success': False,
            'error': {
                'code': 400, 'message': 'This service requires a json to be posted as a payload.'
            }
        },
                         response.json)

    def test_create_shortlink_no_url(self):
        response = self.app.post(
            "/",
            data=json.dumps({}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual("application/json", response.content_type)
        self.assertEqual({
            'success': False,
            'error': {
                'code': 400, 'message': 'Url parameter missing from request'
            }
        },
                         response.json)

    def test_create_shortlink_no_hostname(self):
        wrong_url = "/test"
        response = self.app.post(
            "/",
            data=json.dumps({"url": f"{wrong_url}"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(
            response.json,
            {
                'success': False,
                'error': {
                    'code': 400, 'message': f'URL({wrong_url}) given as parameter is not valid.'
                }
            }
        )

    def test_create_shortlink_non_allowed_hostname(self):
        response = self.app.post(
            "/",
            data=json.dumps({"url": "https://non-allowed.hostname.ch/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(
            response.json,
            {
                'success': False,
                'error': {
                    'code': 400, 'message': 'URL given as a parameter is not allowed.'
                }
            }
        )

    def test_create_shortlink_url_too_long(self):
        url = self.invalid_urls_list[0]
        response = self.app.post(
            "/",
            data=json.dumps({"url": url}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(
            response.json,
            {
                'success': False,
                'error': {
                    'code': 400,
                    'message':
                        "The url given as parameter was too long. "
                        "(limit is 2046 characters, 2946 given)"
                }
            }
        )

    def test_redirect_shortlink_ok(self):
        for shortid, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                f"/{shortid}?redirect=true",
                content_type="text/html",
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response.content_type, "text/html; charset=utf-8")
            TestCase().assertRedirects(response, url)

    def test_shortlink_fetch_nok_invalid_redirect_parameter(self):
        for shortid, _ in self.uuid_to_url_dict.items():
            response = self.app.get(
                f"/{shortid}?redirect=banana",
                content_type="text/html",
                headers={"Origin": "map.geo.admin.ch"}
            )
            expected_json = {
                'success': False,
                'error': {
                    'code': 400,
                    'message': "accepted values for redirect parameter are true or false."
                }
            }
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content_type, "application/json")
            self.assertEqual(response.json, expected_json)

    def test_redirect_shortlink_url_not_found(self):
        response = self.app.get(
            "/nonexistent",
            content_type="text/html; charset=utf-8",
            headers={"Origin": "map.geo.admin.ch"}
        )
        expected_json = {
            'success': False,
            'error': {
                'code': 404,
                'message': "This short url doesn't exist: "
                           "http://localhost/nonexistent"
            }
        }
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, expected_json)

    def test_fetch_full_url_from_shortlink_ok(self):
        for shortid, url in self.uuid_to_url_dict.items():
            response = self.app.get(f"/{shortid}", headers={"Origin": "map.geo.admin.ch"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertEqual(response.json, {'shorturl': shortid, 'full_url': url, 'success': True})

    def test_fetch_full_url_from_shortlink_ok_explicit_parameter(self):
        for shortid, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                f"/{shortid}?redirect=false", headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertEqual(response.json, {'shorturl': shortid, 'full_url': url, 'success': True})

    def test_fetch_full_url_from_shortlink_url_not_found(self):
        response = self.app.get(
            "/nonexistent?redirect=false", headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, "application/json")
        expected_json = {
            'error': {
                'code': 404,
                'message': "This short url doesn't exist: "
                           "http://localhost/nonexistent"
            },
            'success': False
        }
        self.assertEqual(response.json, expected_json)


if __name__ == '__main__':
    unittest.main()
