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
ALLOWED_DOMAINS_PATTERN = '({})'.format('|'.join(ALLOWED_DOMAINS))
AWS_DYNAMODB_TABLE_NAME = os.environ.get('AWS_DYNAMODB_TABLE_NAME')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-central-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', None)
