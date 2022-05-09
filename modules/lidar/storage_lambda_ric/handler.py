from enum import Enum
from functools import wraps
from routes import app
import logging


logger = logging.getLogger(__name__)


class Handler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._stateless_actions = {}
        self._stateful_actions = {}

    def stateless_action(self, name, callable_):
        self._stateless_actions[name] = callable_

    def stateful_action(self, name, calc_parts_callable, callable_):
        self._stateful_actions[name] = calc_parts_callable, callable_

    def _get_stateless_action(self, name, context, kwargs):
        return self._stateless_actions[name](context, **kwargs)

    def _get_stateful_action(self, name, context, kwargs):
        return self._stateful_actions[name](context, **kwargs)

    def serve(self):
        app.action_handler = self
        app.run(host=self.host, port=self.port)


class Method(Enum):
    PUT = "PUT"
    GET = "GET"


class Context:
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
