import logging
import time

from flask import abort
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import url_for

from app import app
from app.helpers.dynamo_db import get_db
from app.helpers.utils import get_redirect_param
from app.helpers.utils import get_url
from app.version import APP_VERSION

logger = logging.getLogger(__name__)


@app.route('/checker', methods=['GET'])
def checker():
    logger.debug("Checker route entered at %f", time.time())
    response = make_response(
        jsonify({
            'success': True, 'message': 'OK', 'version': APP_VERSION
        }), 200
    )
    return response


@app.route('/', methods=['POST'])
def create_shortlink():
    """Create a new shortlink if needed otherwiser return existing
    """
    new_entry = False
    url = get_url()
    db = get_db()
    db_entry = db.get_entry_by_url(url)
    if db_entry is None:
        db_entry = db.add_url_to_table(url)
        new_entry = True

    response = make_response(
        jsonify({
            "shorturl":
                url_for("get_shortlink", shortlink_id=db_entry['shortlink_id'], _external=True),
            'success': True
        }),
        201 if new_entry else 200
    )

    logger.info("Shortlink Creation Successful.", extra={"response": {"json": response.get_json()}})
    return response


@app.route('/<shortlink_id>', methods=['GET'])
def get_shortlink(shortlink_id):
    """
    This route checks the shortened url id  and redirect the user to the full url.
    When the redirect query parameter is set to false, it will return a json containing
    the information about the shortlink.
    """
    should_redirect = get_redirect_param()
    db_entry = get_db().get_entry_by_shortlink(shortlink_id)
    if db_entry is None:
        abort(404, f'No short url found for {shortlink_id}')

    if should_redirect:
        logger.info("redirecting to the following url : %s", db_entry['url'])
        return redirect(db_entry['url'], code=301)

    return make_response(
        jsonify({
            'shorturl': shortlink_id,
            'url': db_entry['url'],
            'created': db_entry['created'],
            'success': True
        })
    )
