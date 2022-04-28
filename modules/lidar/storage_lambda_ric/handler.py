from enum import Enum


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
                 key=None,
                 bucket=None,
                 content_type=None,
                 cache=None,
                 method=None):
        self.request = request
        self.response = response
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.redis_client = redis_client
        self.key = key
        self.bucket = bucket
        self.content_type = content_type
        self.full_key = '/' + bucket + '/' + key
        self.cache = cache
        self.method = method
    
    def preprocess(self):
        raise NotImplementedError()
