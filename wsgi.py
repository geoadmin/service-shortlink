import os

from app.helpers import get_logging_cfg
"""
    The gevent monkey import and patch suppress a warning, and a potential problem.
    Gunicorn would call it anyway, but if it tries to call it after the ssl module
    has been initialised in another module (like, in our code, by the botocore library),
    then it could lead to inconcistencies in how the ssl module is used. Thus we patch
    the ssl module through gevent.monkey.patch_all before any other import, especially
    the app import, which would cause the boto module to be loaded, which would in turn
    load the ssl module.
"""
import gevent.monkey  # pylint: disable=wrong-import-position,wrong-import-order

gevent.monkey.patch_all()
from gunicorn.app.base import BaseApplication  # pylint: disable=wrong-import-position,wrong-import-order
from app import app as application  # pylint: disable=wrong-import-position,ungrouped-imports


class StandaloneApplication(BaseApplication):  # pylint: disable=abstract-method

    def __init__(self, app, options=None):  # pylint: disable=redefined-outer-name
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = {
            key: value for key,
            value in self.options.items() if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


# We use the port 8080 as default, otherwise we set the HTTP_PORT env variable within the container.
if __name__ == '__main__':
    HTTP_PORT = str(os.environ.get('HTTP_PORT', "8080"))
    # Bind to 0.0.0.0 to let your app listen to all network interfaces.
    options = {
        'bind': '%s:%s' % ('0.0.0.0', HTTP_PORT),
        'worker_class': 'gevent',
        'workers': 2,  # scaling horizontaly is left to Kubernetes
        'timeout': 60,
        'logconfig_dict': get_logging_cfg()
    }
    StandaloneApplication(application, options).run()
