from enum import Enum
import logging
import os

import boto3
from botocore.client import Config
import redis

logger = logging.getLogger(__name__)


class Method(Enum):
    PUT = "PUT"
    GET = "GET"


class StatelessContext:
    def __init__(self,
                 input_stream=None,
                 output_stream=None,
                 key=None,
                 bucket=None,
                 content_type=None,
                 method=None):
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.key = key
        self.bucket = bucket
        self.content_type = content_type
        self.full_key = '/' + bucket + '/' + key
        self.method = method

        self.s3_client = None
        self.redis_client = None

    def get_s3_client(self):
        if self.s3_client is None:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.environ['S3_ENDPOINT_URL'],
                aws_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
                aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY'],
                config=Config(signature_version='s3v4'),
                region_name='us-east-1'
            )
        return self.s3_client

    def get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.Redis(
                host=os.environ['REDIS_HOST'],
                port=int(os.environ.get('REDIS_PORT', '6379')),
                password=os.environ.get('REDIS_PASSWORD', None),
                db=int(os.environ.get('REDIS_DB', '0'))
            )
        return self.redis_client

    def do_get(self, byte_range=None):
        if self.method == Method.GET:
            logger.debug('Performing GET to S3 %s/%s', self.bucket, self.key)
            client = self.get_s3_client()
            if byte_range is not None:
                s3_response = client.get_object(
                    Bucket=self.bucket, Key=self.key,
                    Range=f'bytes={byte_range[0]}-{byte_range[1]}')
            else:
                s3_response = client.get_object(Bucket=self.bucket, Key=self.key)
            streaming_body = s3_response['Body']
            self.input_stream = streaming_body
        elif self.method == Method.PUT:
            logger.debug(f'Input stream already inbound')


class StatefulContext(StatelessContext):
    def __init__(self, output_streams, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_streams = output_streams
