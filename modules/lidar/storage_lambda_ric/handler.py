from enum import Enum
import logging


logger = logging.getLogger(__name__)


class Method(Enum):
    PUT = "PUT"
    GET = "GET"


class HandlerBase:
    def __init__(self,
                 request=None,
                 response=None,
                 input_stream=None,
                 output_stream=None,
                 redis_client=None,
                 s3_client=None,
                 key=None,
                 bucket=None,
                 content_type=None,
                 method=None):
        self.request = request
        self.response = response
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.redis_client = redis_client
        self.s3_client = s3_client
        self.key = key
        self.bucket = bucket
        self.content_type = content_type
        self.full_key = '/' + bucket + '/' + key
        self.method = method

    async def do_get(self):
        if self.method == Method.GET:
            logger.debug(f'Performing GET to S3 (bucket={self.bucket}, key={self.key})')
            s3_response = await self.s3_client.get_object(Bucket=self.bucket, Key=self.key)
            streaming_body = s3_response['Body']
            self.input_stream = streaming_body
        elif self.method == Method.PUT:
            logger.debug(f'Input stream already inbound')
