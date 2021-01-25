import os
import logging
import logging.config

import yaml

logger = logging.getLogger(__name__)


def get_logging_cfg():
    cfg_file = os.getenv('LOGGING_CFG', 'logging-cfg-local.yaml')

    config = {}
    with open(cfg_file, 'rt') as fd:
        config = yaml.safe_load(fd.read())

    logger.debug('Load logging configuration from file %s', cfg_file)
    return config


def init_logging():
    config = get_logging_cfg()
    logging.config.dictConfig(config)
