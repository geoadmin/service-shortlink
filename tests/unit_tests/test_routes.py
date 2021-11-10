import logging
import logging.config
import re

from flask_testing import TestCase

from flask import url_for

from tests.unit_tests.base import BaseShortlinkTestCase

logger = logging.getLogger(__name__)


class TestRoutes(BaseShortlinkTestCase):

    def test_checker_ok(self):
        # checker
        response = self.app.get(url_for('checker'), headers={"Origin": "map.geo.admin.ch"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Cache-Control', response.headers)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json, {'success': True, 'message': 'OK'})

    def test_create_shortlink_ok(self):
        response = self.app.post(
            url_for('create_shortlink'),
            json={"url": "https://map.geo.admin.ch/test"},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json.get('success'), True)
        shorturl = response.json.get('shorturl')
        self.assertEqual('http://localhost/' in shorturl, True)
        shorturl = shorturl.replace('http://localhost/', '')
        self.assertEqual(re.search(r"^\d{12}$", shorturl) is not None, True)

    def test_create_shortlink_no_json(self):
        response = self.app.post(
            url_for('create_shortlink'), headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('application/json', response.content_type)
        self.assertEqual({
            'success': False,
            'error': {
                'code': 400, 'message': 'This service requires a json to be posted as a payload.'
            }
        },
                         response.json)

    def test_create_shortlink_no_url(self):
        response = self.app.post(
            url_for('create_shortlink'), json={}, headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('application/json', response.content_type)
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
            url_for('create_shortlink'),
            json={"url": f"{wrong_url}"},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('application/json', response.content_type)
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
            url_for('create_shortlink'),
            json={"url": "https://non-allowed.hostname.ch/test"},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('application/json', response.content_type)
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
            url_for('create_shortlink'),
            json={"url": url},
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('application/json', response.content_type)
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
                url_for('get_shortlink', shortlink_id=shortid),
                query_string={'redirect': 'true'},
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 301)
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.content_type, "text/html; charset=utf-8")
            TestCase().assertRedirects(response, url)

    def test_shortlink_fetch_nok_invalid_redirect_parameter(self):
        for shortid, _ in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=shortid),
                query_string={'redirect': 'banana'},
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
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=3600', response.headers['Cache-Control'])
            self.assertIn('application/json', response.content_type)
            self.assertEqual(response.json, expected_json)

    def test_redirect_shortlink_url_not_found(self):
        response = self.app.get(
            url_for('get_shortlink', shortlink_id='nonexistent'),
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
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age=3600', response.headers['Cache-Control'])
        self.assertIn('application/json', response.content_type)
        self.assertEqual(response.json, expected_json)

    def test_fetch_full_url_from_shortlink_ok(self):
        for shortid, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=shortid),
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertEqual(response.json, {'shorturl': shortid, 'full_url': url, 'success': True})

    def test_fetch_full_url_from_shortlink_ok_explicit_parameter(self):
        for shortid, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=shortid),
                query_string={'redirect': 'false'},
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.json, {'shorturl': shortid, 'full_url': url, 'success': True})

    def test_fetch_full_url_from_shortlink_url_not_found(self):
        response = self.app.get(
            url_for('get_shortlink', shortlink_id='nonexistent'),
            query_string={'redirect': 'false'},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age=3600', response.headers['Cache-Control'])
        self.assertIn('application/json', response.content_type)
        expected_json = {
            'error': {
                'code': 404,
                'message': "This short url doesn't exist: "
                           "http://localhost/nonexistent"
            },
            'success': False
        }
        self.assertEqual(response.json, expected_json)

    def test_create_shortlink_no_origin_header(self):
        response = self.app.post("/")
        self.assertEqual(403, response.status_code)
        self.assertIn('application/json', response.content_type)
        self.assertEqual({
            'success': False, 'error': {
                'code': 403, 'message': 'Permission denied'
            }
        },
                         response.json)

    def test_create_shortlink_non_allowed_origin_header(self):
        response = self.app.post("/", headers={"Origin": "big-bad-wolf.com"})
        self.assertEqual(403, response.status_code)
        self.assertIn('application/json', response.content_type)
        self.assertEqual({
            'success': False, 'error': {
                'code': 403, 'message': 'Permission denied'
            }
        },
                         response.json)
