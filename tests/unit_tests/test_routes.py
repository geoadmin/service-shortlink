import logging
import logging.config
import re

from nose2.tools import params

from flask import url_for

from app.settings import SHORT_ID_ALPHABET
from app.settings import SHORT_ID_SIZE
from app.version import APP_VERSION
from tests.unit_tests.base import BaseShortlinkTestCase

logger = logging.getLogger(__name__)


class TestRoutes(BaseShortlinkTestCase):

    def test_checker_ok(self):
        # checker
        response = self.app.get(url_for('checker'), headers={"Origin": "map.geo.admin.ch"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Cache-Control', response.headers)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json, {'success': True, 'message': 'OK', 'version': APP_VERSION})

    def test_create_shortlink_ok(self):
        url = "https://map.geo.admin.ch/#/map?lang=en&center=2647850.83,1120124.2&z=1.812&bgLayer=ch.swisstopo.pixelkarte-farbe&top"  # pylint: disable=line-too-long
        response = self.app.post(
            url_for('create_shortlink'), json={"url": url}, headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertCors(response, ['POST', 'OPTIONS'])
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json.get('success'), True)
        shorturl = response.json.get('shorturl')
        self.assertEqual('http://localhost/' in shorturl, True)
        short_id = shorturl.replace('http://localhost/', '')
        self.assertEqual(
            len(short_id),
            SHORT_ID_SIZE,
            msg=f"Length of short_id '{short_id}' does not match configured size of "\
                f"{SHORT_ID_SIZE} characters"
        )
        # Check if all characters of short_id are allowed characters as defined in SHORT_ID_ALPHABET
        self.assertIsNotNone(
            re.fullmatch(f"[{SHORT_ID_ALPHABET}]+", short_id),
            f"Invalid characters found in short-id '{short_id}'. Allowed '{SHORT_ID_ALPHABET}'"
        )
        # Check that second call returns 200 and the same short url
        response = self.app.post(
            url_for('create_shortlink'), json={"url": url}, headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertCors(response, ['POST', 'OPTIONS'])
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json.get('success'), True)
        self.assertEqual(response.json.get('shorturl'), shorturl)

    def test_create_shortlink_no_json(self):
        response = self.app.post(
            url_for('create_shortlink'), headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(415, response.status_code)
        self.assertCors(response, ['POST', 'OPTIONS'])
        self.assertIn('application/json', response.content_type)
        self.assertEqual(
            {
                'success': False,
                'error': {
                    'code': 415,
                    'message': 'Input data missing or from wrong type, must be application/json'
                }
            },
            response.json,
        )

    def test_create_shortlink_no_url(self):
        response = self.app.post(
            url_for('create_shortlink'), json={}, headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(400, response.status_code)
        self.assertCors(response, ['POST', 'OPTIONS'])
        self.assertIn('application/json', response.content_type)
        self.assertEqual(
            {
                'success': False,
                'error': {
                    'code': 400, 'message': 'Url parameter missing from request'
                }
            },
            response.json,
        )

    def test_create_shortlink_no_hostname(self):
        wrong_url = "/test"
        response = self.app.post(
            url_for('create_shortlink'),
            json={"url": f"{wrong_url}"},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertCors(response, ['POST', 'OPTIONS'])
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
        self.assertCors(response, ['POST', 'OPTIONS'])
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

    def test_create_shortlink_non_allowed_hostname_containing_admin_address(self):
        response = self.app.post(
            url_for('create_shortlink'),
            json={"url": "https://map.geo.admin.ch.non-allowed.hostname.ch/test"},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertCors(response, ['POST', 'OPTIONS'])
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
        self.assertCors(response, ['POST', 'OPTIONS'])
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
        for short_id, url in self.uuid_to_url_dict.items():
            response = self.app.get(url_for('get_shortlink', shortlink_id=short_id))
            self.assertEqual(response.status_code, 301)
            self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'], origin_pattern=r"^\*$")
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.content_type, "text/html; charset=utf-8")
            self.assertRedirects(response, url)

    def test_redirect_shortlink_ok_with_query(self):
        for short_id, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=short_id),
                query_string={'redirect': 'true'},
                headers={"Origin": "www.example.com"}
            )
            self.assertEqual(response.status_code, 301)
            self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'], origin_pattern=r"^\*$")
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.content_type, "text/html; charset=utf-8")
            self.assertRedirects(response, url)

    def test_shortlink_fetch_nok_invalid_redirect_parameter(self):
        for short_id, _ in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=short_id),
                query_string={'redirect': 'banana'},
                content_type="text/html",
                headers={"Origin": "map.geo.admin.ch"}
            )
            expected_json = {
                'success': False,
                'error': {
                    'code': 400,
                    'message': "Invalid \"redirect\" arg: invalid truth value 'banana'"
                }
            }
            self.assertEqual(response.status_code, 400)
            self.assertCors(
                response,
                ['GET', 'HEAD', 'OPTIONS'],
            )
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=3600', response.headers['Cache-Control'])
            self.assertIn('application/json', response.content_type)
            self.assertEqual(response.json, expected_json)

    def test_redirect_shortlink_url_not_found(self):
        response = self.app.get(
            url_for('get_shortlink', shortlink_id='nonexistent'),
            headers={"Origin": "map.geo.admin.ch"}
        )
        expected_json = {
            'success': False,
            'error': {
                'code': 404, 'message': "No short url found for nonexistent"
            }
        }
        self.assertEqual(response.status_code, 404)
        self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'], origin_pattern=r"^\*$")
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age=3600', response.headers['Cache-Control'])
        self.assertIn('application/json', response.content_type)
        self.assertEqual(response.json, expected_json)

    def test_fetch_full_url_from_shortlink_ok(self):
        for short_id, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=short_id),
                query_string={'redirect': 'false'},
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'])
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertEqual(response.json['success'], True)
            self.assertEqual(response.json['shorturl'], short_id)
            self.assertEqual(response.json['url'], url)

    def test_fetch_full_url_from_shortlink_ok_explicit_parameter(self):
        for short_id, url in self.uuid_to_url_dict.items():
            response = self.app.get(
                url_for('get_shortlink', shortlink_id=short_id),
                query_string={'redirect': 'false'},
                headers={"Origin": "map.geo.admin.ch"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'])
            self.assertEqual(response.content_type, "application/json; charset=utf-8")
            self.assertIn('Cache-Control', response.headers)
            self.assertIn('max-age=', response.headers['Cache-Control'])
            self.assertEqual(response.json['success'], True)
            self.assertEqual(response.json['shorturl'], short_id)
            self.assertEqual(response.json['url'], url)

    def test_fetch_full_url_from_shortlink_url_not_found(self):
        response = self.app.get(
            url_for('get_shortlink', shortlink_id='nonexistent'),
            query_string={'redirect': 'false'},
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'])
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age=3600', response.headers['Cache-Control'])
        self.assertIn('application/json', response.content_type)
        expected_json = {
            'error': {
                'code': 404, 'message': "No short url found for nonexistent"
            },
            'success': False
        }
        self.assertEqual(response.json, expected_json)

    @params(
        None,
        {'Origin': 'www.example'},
        {'Origin': 'map.geo.admin.ch.non-allowed.hostname.ch'},
        {'Origin': ''},
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'cross-site'
        },
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'same-site'
        },
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'same-origin'
        },
        {'Referer': 'map.geo.admin.ch.non-allowed.hostname.ch'},
        {'Referer': 'http://www.example'},
        {'Referer': ''},
    )
    def test_create_shortlink_origin_not_allowed(self, headers):
        response = self.app.post("/", headers=headers)
        self.assertEqual(403, response.status_code)
        self.assertCors(response, ['POST', 'OPTIONS'])
        self.assertIn('application/json', response.content_type)
        self.assertEqual(
            {
                'success': False, 'error': {
                    'code': 403, 'message': 'Permission denied'
                }
            },
            response.json,
        )

    @params(
        {'Origin': 'map.geo.admin.ch'},
        {
            'Origin': 'map.geo.admin.ch', 'Sec-Fetch-Site': 'same-site'
        },
        {
            'Origin': 's.geo.admin.ch', 'Sec-Fetch-Site': 'same-origin'
        },
        {
            'Origin': 'http://localhost', 'Sec-Fetch-Site': 'cross-site'
        },
        {'Sec-Fetch-Site': 'same-origin'},
        {'Referer': 'https://map.geo.admin.ch'},
    )
    def test_create_shortlink_origin_allowed(self, headers):
        url = "https://map.geo.admin.ch/test"
        response = self.app.post(url_for('create_shortlink'), json={"url": url}, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertCors(response, ['POST', 'OPTIONS'])
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.json.get('success'), True)

    @params(
        None,
        {},
        {'Origin': "www.example"},
        {'Origin': 'map.geo.admin.ch'},
        {'Origin': ''},
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'cross-site'
        },
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'same-site'
        },
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'same-origin'
        },
        {
            'Origin': 'www.example', 'Sec-Fetch-Site': 'none'
        },
        {
            'Origin': 'map.geo.admin.ch', 'Sec-Fetch-Site': 'same-site'
        },
        {
            'Origin': 's.geo.admin.ch', 'Sec-Fetch-Site': 'same-origin'
        },
        {
            'Origin': 'http://localhost', 'Sec-Fetch-Site': 'cross-site'
        },
        {'Referer': 'http://www.example'},
        {'Referer': 'https://map.geo.admin.ch'},
        {'Referer': ''},
        {'Sec-Fetch-Site': 'same-origin'},
        {'Sec-Fetch-Site': 'same-site'},
        {'Sec-Fetch-Site': 'none'},
        {'Sec-Fetch-Site': 'cross-site'},
    )
    def test_get_shortlink_redirect_origin_allowed(self, headers):
        short_id = next(iter(self.uuid_to_url_dict.keys()))
        response = self.app.get(
            url_for('get_shortlink', shortlink_id=short_id),
            query_string={'redirect': 'true'},
            headers=headers
        )
        self.assertEqual(response.status_code, 301)
        self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'], origin_pattern=r"^\*$")

        response = self.app.get(url_for('get_shortlink', shortlink_id=short_id), headers=headers)
        self.assertEqual(response.status_code, 301)
        self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'], origin_pattern=r"^\*$")

    @params(
        {'Origin': 'map.geo.admin.ch'},
        {
            'Origin': 'map.geo.admin.ch', 'Sec-Fetch-Site': 'same-site'
        },
        {
            'Origin': 's.geo.admin.ch', 'Sec-Fetch-Site': 'same-origin'
        },
        {
            'Origin': 'http://localhost', 'Sec-Fetch-Site': 'cross-site'
        },
        {'Sec-Fetch-Site': 'same-origin'},
        {'Sec-Fetch-Site': 'same-site'},
        {'Referer': 'https://map.geo.admin.ch'},
    )
    def test_get_shortlink_origin_allowed(self, headers):
        short_id = next(iter(self.uuid_to_url_dict.keys()))
        response = self.app.get(
            url_for('get_shortlink', shortlink_id=short_id),
            query_string={'redirect': 'false'},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertCors(response, ['GET', 'HEAD', 'OPTIONS'])
