from flask import jsonify
from flask import make_response


def make_error_msg(code, msg):
    """
    * Quick summary of the function *
    * Abortions originating in this function *
    * Abortions originating in functions called from this function *
    * Parameters and return values *
    """
    return make_response(jsonify({'success': False, 'error': {'code': code, 'message': msg}}), code)
