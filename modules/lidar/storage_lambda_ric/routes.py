from lidar import LASModule
import traceback
import os
import logging
from aiobotocore.session import AioSession
from sanic import Sanic
from sanic.response import json
from redis import asyncio as aioredis

from .handler import Context, Method
from .streamwriter import MultipartUploader, StreamResponseWrapper

app = Sanic(name="test")
logger = logging.getLogger(__name__)


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

        multipart_writer = MultipartUploader(
            s3_client, bucket, key, content_type=content_type)
        await multipart_writer._setup()

        mod = LASModule(request=request,
                        input_stream=request.stream,
                        output_stream=multipart_writer,
                        redis_client=redis_client,
                        key=key,
                        bucket=bucket,
                        content_type=content_type,
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
    action_type = request.headers['amz-s3proxy-action-type']
    kwargs = {k: v.pop() for k, v in request.args.items()}

    logger.info('GET %s %s %s %s', function_name, bucket, key, str(kwargs))

    if action_type == "stateless":
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

            response_stream = StreamResponseWrapper(response)

            context = Context(request=request,
                              response=response,
                              output_stream=response_stream,
                              redis_client=redis_client,
                              s3_client=s3_client,
                              key=key,
                              bucket=bucket,
                              content_type=content_type,
                              method=Method.GET)
            try:
                action_callable = app.action_handler._get_stateless_action(function_name)
                await action_callable(context, **kwargs)
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(tb)
                raise e
        response = await request.respond(content_type=content_type)
    elif action_type == "stateful":
        response = await request.respond(content_type="application/json")
        
        calc_parts_callable, action_callable = app.action_handler._get_stateless_action(function_name)
        parts = calc_parts_callable(None, **kwargs)

        await response.send(json.dumps({'parts': parts}).encode('utf-8'))
        await response.eof()
        
        await action_callable(context, **kwargs)



    else:
        raise Exception(f"Unknown action type {action_type}")
