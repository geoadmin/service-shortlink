import json
import unittest
from flask import make_response
from flask import jsonify
from app import app
from app import routes

"""
    TODO :
        1. Create fake dynamodb and populate it
        2. Mock 'get_dynamodb()' call to return the fake db
        3. for each call, 
"""

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_checker_ok(self):
        # checker
        self.setUp()
        response = self.app.get(
            f"/checker", headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {'success': True, 'message': 'OK'})

    def test_create_shortlink_ok(self):
        self.setUp()
        response = self.app.post(
            f"/create_shortlink",
            data=json.dumps({"url": "https://map.geo.admin.ch/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {'success': True, 'shorturl': ""})


    """
    The following tests should all return a 400 error code
    """
    def test_create_shortlink_no_url(self):
        self.setUp()
        response = self.app.post(
            f"/create_shortlink",
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {'success': True, 'shorturl': ""})

    def test_create_shortlink_no_hostname(self):
        self.setUp()
        response = self.app.post(
            f"/create_shortlink",
            data=json.dumps({"url": "/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {'success': True, 'shorturl': ""})

    def test_create_shortlink_non_allowed_hostname_and_domain(self):
        self.setUp()
        response = self.app.post(
            f"/create_shortlink",
            data=json.dumps({"url": "https://not.a.valid.hostname.ch/test"}),
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {'success': True, 'shorturl': ""})

    def test_create_shortlink_url_too_long(self):
        self.setUp()
        response = self.app.post(
            f"/create_shortlink",
            data=json.dumps({"url": "https://map.geo.admin.ch/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/ThisIsAVeryLongTextWhoseGoalIsToMakeSureWeGoOverThe2046CharacterLimitOfTheServiceShortlinkUrl/ThisWillNowBeCopiedMultipleTimes/"}),  # pylint: disable=line-too-long
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {'success': True, 'shorturl': ""})

    def test_redirect_shortlink_ok(self):
        self.setUp()
        response = self.app.get(
            f"/redirect_shortlink/1578091241",
            content_type="text/html",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.content_type, "text/html")
        self.assertEqual(response.url, "blabla")

    # The following test will return a 404
    def test_redirect_shortlink_url_not_found(self):
        self.setUp()
        response = self.app.get(
            f"/redirect_shortlink/nonexistent",
            content_type="text/html",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, "text/html")
        self.assertEqual(response.url, "blabla")

    # The following test will return a 404
    def fetch_full_url_from_shortlink_ok(self):
        self.setUp()
        response = self.app.get(
            f"/1578091241",
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {
            'shorturl': "1578091241",
            'full_url': "url",
            'success': True
        })

    def test_fetch_full_url_from_shortlink_url_not_found(self):
        self.setUp()
        response = self.app.get(
            f"/1578091241",
            content_type="application/json",
            headers={"Origin": "map.geo.admin.ch"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json, {
            'shorturl': "1578091241",
            'full_url': "url",
            'success': True
        })


if __name__ == '__main__':
    unittest.main()
