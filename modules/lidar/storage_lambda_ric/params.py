import os
from dataclasses import dataclass


@dataclass
class Params:
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_endpoint_url: str
    redis_url: str
    redis_password: str


GLOBAL_PARAMS = None

