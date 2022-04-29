from lidar import LASModule
import traceback
import os
import logging
from aiobotocore.session import AioSession
from sanic import Sanic
from sanic.response import json
from redis import asyncio as aioredis
from diskcache import Cache

from .handler import Method
from .streamwriter import MultipartUploader, StreamResponseWrapper

app = Sanic(name="test")
logger = logging.getLogger(__name__)

cache = Cache("/tmp/diskcache")


@app.route('/apply/<function_name:str>', methods=["PUT"], stream=True)
async def apply_on_put(request, function_name):
    session = AioSession()

    bucket = request.headers['amz-s3proxy-bucket']
    key = request.headers['amz-s3proxy-key']
    content_type = request.headers['Content-Type']
    kwargs = {k: v.pop() for k, v in request.args.items()}

    logger.info('PUT %s %s %s %s', function_name, bucket, key, str(kwargs))

    redis_client = await aioredis.from_url(
        'redis://'+os.environ['REDIS_HOST'],
        password=os.environ['REDIS_PASSWORD']
    )

    async with session.create_client(
        's3',
        endpoint_url=os.environ['S3_ENDPOINT_URL'],
        aws_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY']
    ) as s3_client:

        multipart_writer = MultipartUploader(s3_client, bucket, key, content_type=content_type)
        await multipart_writer._setup()

        mod = LASModule(request=request,
                        input_stream=request.stream,
                        output_stream=multipart_writer,
                        redis_client=redis_client,
                        key=key,
                        bucket=bucket,
                        content_type=content_type,
                        cache=cache,
                        method=Method.PUT)
        try:
            func = getattr(mod, function_name)
            await func(**kwargs)
        except Exception as e:
            traceback.print_exc()
            await multipart_writer.abort_upload()
            raise e

    return json({'etag': multipart_writer.etag})


@app.route('/apply/<function_name:str>', methods=["GET"], stream=True)
async def apply_on_get(request, function_name):
    session = AioSession()

    bucket = request.headers['amz-s3proxy-bucket']
    key = request.headers['amz-s3proxy-key']
    content_type = request.headers['amz-s3proxy-content-type']
    kwargs = {k: v.pop() for k, v in request.args.items()}

    logger.info('GET %s %s %s %s', function_name, bucket, key, str(kwargs))

    response = await request.respond(content_type=content_type)

    redis_client = await aioredis.from_url(
        'redis://'+os.environ['REDIS_HOST'],
        password=os.environ['REDIS_PASSWORD']
    )

    async with session.create_client(
        's3',
        endpoint_url=os.environ['S3_ENDPOINT_URL'],
        aws_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY']
    ) as s3_client:

        s3_response = await s3_client.get_object(Bucket=bucket, Key=key)
        streaming_body = s3_response['Body']
        response_stream = StreamResponseWrapper(response)

        mod = LASModule(request=request,
                        response=response,
                        input_stream=streaming_body,
                        output_stream=response_stream,
                        redis_client=redis_client,
                        key=key,
                        bucket=bucket,
                        content_type=content_type,
                        cache=cache,
                        method=Method.GET)
        try:
            func = getattr(mod, function_name)
            await func(**kwargs)
        except Exception as e:
            traceback.print_exc()
            raise e
