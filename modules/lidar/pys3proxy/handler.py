

class HandlerBase:
    def __init__(self,
                 request=None,
                 response=None,
                 input_stream=None,
                 output_stream=None,
                 redis_client=None):
        self.request = request
        self.response = response
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.redis_client = redis_client
    
    def preprocess(self):
        raise NotImplementedError()
