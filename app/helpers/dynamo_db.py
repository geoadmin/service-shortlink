import json
import logging
import logging.config
from datetime import datetime
from datetime import timezone

import boto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key

from flask import g

from app.helpers.utils import generate_short_id
from app.settings import AWS_DEFAULT_REGION
from app.settings import AWS_DYNAMODB_TABLE_NAME
from app.settings import AWS_ENDPOINT_URL
from app.settings import COLLISION_MAX_RETRY
from app.settings import STAGING

logger = logging.getLogger(__name__)


def get_db():
    if 'db' not in g:
        g.db = DynamoDB()
    return g.db


class DynamoDB():

    def __init__(self):
        self.resource = boto3.resource(
            'dynamodb', region_name=AWS_DEFAULT_REGION, endpoint_url=AWS_ENDPOINT_URL
        )
        self.table = self.resource.Table(AWS_DYNAMODB_TABLE_NAME)

    def get_entry_by_url(self, url):
        """Get a DB entry by full url

        Arguments:
            url: str
                full url to get from DB

        Returns:
            Table entry or None if ULR is not found in Table
        """
        response = self.table.query(
            IndexName="UrlIndex",
            KeyConditionExpression=Key('url').eq(url),
        )
        try:
            return response['Items'][0]
        except IndexError:
            logger.debug(
                "The following url '%s' was not found in dynamodb",
                url,
                extra={"db_response": response}
            )
            return None

    def get_entry_by_shortlink(self, short_id):
        '''Get an entry by shortlink_id

        Args:
            short_id: str
                shortlink_id to get from the table
        Returns:
            Table entry or None if shortlink_id is not found in Table
        '''
        response = self.table.get_item(Key={'shortlink_id': short_id})
        try:
            return response['Item']
        except KeyError:
            logger.error(
                'The following shortlink_id not found in dynamodb: %s',
                short_id,
                extra={"db_response": response}
            )
            return None

    def add_url_to_table(self, url):
        '''Add URL in table

        Args:
            url: string
                URL to add to table

        Returns:
            Table entry
        '''
        now = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
        collision_retry = 0
        while True:
            try:
                short_id = generate_short_id()
                entry = {'shortlink_id': short_id, 'url': url, 'created': now, 'staging': STAGING}
                logger.debug('Adding DB entry: %s', json.dumps(entry))
                self.table.put_item(
                    Item=entry, ConditionExpression=Attr('shortlink_id').not_exists()
                )
                break
            except self.table.meta.client.exceptions.ConditionalCheckFailedException as error:
                if collision_retry < 1:
                    logger.warning(
                        'Short ID %s collision, retry=%d: %s', short_id, collision_retry, error
                    )
                elif collision_retry < 3:
                    logger.error(
                        'Short ID %s collision, retry=%d: %s', short_id, collision_retry, error
                    )
                elif collision_retry < COLLISION_MAX_RETRY:
                    logger.critical(
                        'Failed to create unique DB entry after %d retries: %s',
                        collision_retry,
                        error
                    )
                else:
                    raise
                collision_retry += 1

        return entry
