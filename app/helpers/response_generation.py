from flask import make_response, jsonify


def make_error_msg(code, msg):
    return make_response(jsonify({'success': False, 'error': {'code': code, 'message': msg}}), code)


def create_response(base_url, short_id, error_message=None):
    response = {"shorturl": base_url + short_id}
    if error_message is not None:
        response["error"] = error_message
    return response
