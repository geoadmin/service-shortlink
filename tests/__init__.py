import logging.config

logging.config.dictConfig({
    "version": 1,
    "loggers": {
        "botocore": {
            "level": "INFO"
        }, "boto3": {
            "level": "INFO"
        }
    },
})
