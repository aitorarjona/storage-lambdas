from dataclasses import dataclass
import traceback
import os
import logging
from aiobotocore.session import AioSession
from sanic import Sanic
from sanic.response import json
from redis import asyncio as aioredis

from .streamwriter import MultipartUploader

app = Sanic(name="test")
logger = logging.getLogger(__name__)

from lidar import LASModule

@dataclass
class Params:
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_endpoint_url: str
    redis_url: str
    redis_password: str

globalParams = Params(
    s3_endpoint_url=os.environ['S3_ENDPOINT_URL'],
    s3_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
    s3_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY'],
    redis_url=os.environ.get('REDIS_URL'),
    redis_password=os.environ.get('REDIS_PASSWORD')
)


@app.route('/preprocess', methods=["POST"], stream=True)
async def preprocess(request):
    global globalParams
    session = AioSession()

    bucket = request.headers['amz-s3proxy-bucket']
    key = request.headers['amz-s3proxy-obj-key']
    content_type = request.headers['Content-Type']

    redis_client = await aioredis.from_url(
        globalParams.redis_url,
        password=globalParams.redis_password
    )

    async with session.create_client(
        's3', endpoint_url=globalParams.s3_endpoint_url,
            aws_access_key_id=globalParams.s3_access_key_id,
            aws_secret_access_key=globalParams.s3_secret_access_key) as s3_client:

        multipart_writer = MultipartUploader(s3_client, bucket, key, content_type=content_type)
        await multipart_writer._setup()

        mod = LASModule(request=request, output_stream=multipart_writer, redis_client=redis_client)
        try:
            await mod.preprocess()
        except Exception as e:
            await multipart_writer.abort_upload()
            raise e

    return json({'etag': multipart_writer.etag})


@app.route('/apply/<function_name:str>', methods=["GET"], stream=True)
async def apply(request, function_name):
    global globalParams
    session = AioSession()

    bucket = request.headers['amz-s3proxy-bucket']
    key = request.headers['amz-s3proxy-key']
    kwargs = {k: v.pop() for k, v in request.args.items()}

    logger.info('GET %s %s %s %s', function_name, bucket, key, str(kwargs))
    # print(globalParams)

    # redis_client = await aioredis.from_url(
    #     globalParams.redis_url,
    #     password=globalParams.redis_password
    # )
    redis_client = None
    response = await request.respond(content_type="application/octet-stream")

    async with session.create_client(
        's3', endpoint_url=globalParams.s3_endpoint_url,
            aws_access_key_id=globalParams.s3_access_key_id,
            aws_secret_access_key=globalParams.s3_secret_access_key) as s3_client:

        s3_response = await s3_client.get_object(Bucket=bucket, Key=key)

        streaming_body = s3_response['Body']
        mod = LASModule(request=request, response=response,
                        input_stream=streaming_body,
                        redis_client=redis_client)
        try:
            func = getattr(mod, function_name)
            await func(**kwargs)
        except Exception as e:
            traceback.print_exc()

    await response.eof()
