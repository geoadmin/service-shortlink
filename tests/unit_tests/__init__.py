# The mocking is placed here to make sure it is started earliest possible.
# see: https://github.com/spulec/moto#very-important----recommended-usage
from moto import mock_dynamodb

dynamodb = mock_dynamodb()
dynamodb.start()
