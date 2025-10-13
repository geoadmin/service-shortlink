import os

"""
The Config contains everything needed to run the service. Most entries have a default
value and an environment value to override it.

"""
ENV_FILE = os.getenv('ENV_FILE', None)
if ENV_FILE:
    from dotenv import load_dotenv

    print(f"Running locally hence injecting env vars from {ENV_FILE}")
    load_dotenv(ENV_FILE, override=True, verbose=True)

# Definition of the allowed domains for CORS implementation
ALLOWED_DOMAINS_STRING = os.getenv('ALLOWED_DOMAINS', '.*')
ALLOWED_DOMAINS = ALLOWED_DOMAINS_STRING.split(',')
ALLOWED_DOMAINS_PATTERN = f"({'|'.join(ALLOWED_DOMAINS)})"
AWS_DYNAMODB_TABLE_NAME = os.environ.get('AWS_DYNAMODB_TABLE_NAME')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-central-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', None)

CACHE_CONTROL = os.getenv('CACHE_CONTROL', 'public, max-age=31536000')
CACHE_CONTROL_4XX = os.getenv('CACHE_CONTROL_4XX', 'public, max-age=3600')

STAGING = os.environ['STAGING']

COLLISION_MAX_RETRY = 10

SHORT_ID_SIZE = int(os.getenv('SHORT_ID_SIZE', '12'))
SHORT_ID_ALPHABET = os.getenv('SHORT_ID_ALPHABET', '0123456789abcdefghijklmnopqrstuvwxyz')

GUNICORN_WORKER_TMP_DIR = os.getenv("GUNICORN_WORKER_TMP_DIR", None)

GUNICORN_KEEPALIVE = int(os.getenv('GUNICORN_KEEPALIVE', '2'))
