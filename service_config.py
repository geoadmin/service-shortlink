import os
"""
The Config contains everything needed to run the service. Most entries have a default
value and an environment value to override it.

"""
ALLOWED_DOMAINS = [
    r'.*\.geo\.admin\.ch',
    r'.*bgdi\.ch',
    r'.*\.swisstopo\.cloud',
]

ENV_FILE = os.getenv('ENV_FILE', None)
if ENV_FILE:
    from dotenv import load_dotenv

    print(f"Running locally hence injecting env vars from {ENV_FILE}")
    load_dotenv(ENV_FILE, override=True, verbose=True)

ALLOWED_DOMAINS_PATTERN = '({})'.format('|'.join(ALLOWED_DOMAINS))
aws_table_name = os.environ.get('AWS_DYNAMODB_TABLE_NAME', 'shortlinks_test')
aws_region = os.environ.get('AWS_DYNAMODB_TABLE_REGION', 'eu-central-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')
# allowed_domains_pattern = re.compile(r"^.*\.admin\.ch|.*\.swisstopo\.cloud|.*\.bgdi\.ch$")
