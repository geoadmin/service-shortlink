from flask import jsonify
from flask import make_response


def make_error_msg(code, msg):
    """
    * Quick summary of the function *

    Ensure response messages are json too, according to the swisstopo guidelines

    * Abortions originating in this function *

    None

    * Abortions originating in functions called from this function *

    None

    * Parameters and return values *

    :param code: the HTTP status code of the response
    :param msg: the message to be displayed to our wonderful users
    :return: a flask response in json.
    """
    return make_response(jsonify({'success': False, 'error': {'code': code, 'message': msg}}), code)
