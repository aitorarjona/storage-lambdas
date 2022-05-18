import traceback
import os
import logging
import asyncio
from uuid import uuid4
from multiprocessing import Process, Pipe
from threading import Thread
from aiobotocore.session import AioSession
from sanic import Sanic
from sanic.response import json
from redis import asyncio as aioredis

from .context import StatelessContext, StatefulContext, Method
from .streamwriter import MultipartUploader, StreamResponseWrapper, PipedWriter

app = Sanic(name="test")
logger = logging.getLogger(__name__)


async def _setup_action_context(key, bucket, content_type, call_id, parts,
                                action_name, action_callable, action_args, send_conn):
    logger.debug('Starting background process for action %s - call id %s parts %s',
                 action_name,  call_id, parts)
    redis_host = 'redis://'+os.environ['REDIS_HOST']
    redis_pass = os.environ['REDIS_PASSWORD']
    redis_client = await aioredis.from_url(redis_host, password=redis_pass)

    session = AioSession()
    async with session.create_client(
        's3',
        endpoint_url=os.environ['S3_ENDPOINT_URL'],
        aws_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY']
    ) as s3_client:

        output_streams = [PipedWriter(pipe) for pipe in send_conn]

        context = StatefulContext(output_streams=output_streams,
                                  redis_client=redis_client,
                                  s3_client=s3_client,
                                  key=key,
                                  bucket=bucket,
                                  content_type=content_type,
                                  method=Method.GET)
        try:
            await action_callable(context, **action_args)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(tb)
            raise e


def _call_wrapper(key, bucket, content_type, call_id, parts,
                  action_name, action_callable, action_args, send_conn):
    asyncio.run(_setup_action_context(key, bucket, content_type, call_id, parts,
                action_name, action_callable, action_args, send_conn))


@app.route('/apply/<action_name:str>', methods=["PUT"], stream=True)
async def apply_on_put(request, action_name):
    pass
    # session = AioSession()

    # bucket = request.headers['amz-s3proxy-bucket']
    # key = request.headers['amz-s3proxy-key']
    # content_type = request.headers['Content-Type']
    # kwargs = {k: v.pop() for k, v in request.args.items()}

    # logger.info('PUT %s %s %s %s', action_name, bucket, key, str(kwargs))

    # redis_client = await aioredis.from_url(
    #     'redis://'+os.environ['REDIS_HOST'],
    #     password=os.environ['REDIS_PASSWORD']
    # )

    # async with session.create_client(
    #     's3',
    #     endpoint_url=os.environ['S3_ENDPOINT_URL'],
    #     aws_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
    #     aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY']
    # ) as s3_client:

    #     multipart_writer = MultipartUploader(
    #         s3_client, bucket, key, content_type=content_type)
    #     await multipart_writer._setup()

    #     mod = LASModule(request=request,
    #                     input_stream=request.stream,
    #                     output_stream=multipart_writer,
    #                     redis_client=redis_client,
    #                     key=key,
    #                     bucket=bucket,
    #                     content_type=content_type,
    #                     method=Method.PUT)
    #     try:
    #         func = getattr(mod, action_name)
    #         await func(**kwargs)
    #     except Exception as e:
    #         traceback.print_exc()
    #         await multipart_writer.abort_upload()
    #         raise e

    # return json({'etag': multipart_writer.etag})


@app.route('/apply/<action_name:str>', methods=["GET"], stream=True)
async def apply_on_get(request, action_name):
    session = AioSession()

    bucket = request.headers['amz-s3proxy-bucket']
    key = request.headers['amz-s3proxy-key']
    content_type = request.headers['amz-s3proxy-content-type']
    call_id = request.headers.get('amz-s3proxy-call-id', None)
    part = request.headers.get('amz-s3proxy-part', None)
    kwargs = {k: v.pop() for k, v in request.args.items()}

    logger.info('---------> GET %s %s %s %s %s %s <---------', action_name, bucket, key, str(kwargs), call_id, part)

    if call_id is not None:
        if call_id not in app.ctx.action_handler._current_actions:
            raise Exception('call id not found')
        if part is None:
            raise Exception('part number required')

        part_n = int(part)

        pipe = app.ctx.action_handler._current_actions[call_id]['pipes'][part_n]
        content_type = app.ctx.action_handler._current_actions[call_id]['content_type']

        response = await request.respond(content_type=content_type)

        chunk = pipe.recv()
        while chunk != b"":
            print(f'send chunk of size {len(chunk)} for part {part_n}')
            await response.send(chunk)
            chunk = pipe.recv()
        await response.eof()
        return

    if action_name in app.ctx.action_handler._stateless_actions:
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

            response = await request.respond(content_type=content_type)
            response_stream = StreamResponseWrapper(response)

            context = StatelessContext(output_stream=response_stream,
                                       redis_client=redis_client,
                                       s3_client=s3_client,
                                       key=key,
                                       bucket=bucket,
                                       content_type=content_type,
                                       method=Method.GET)
            try:
                action_callable = app.ctx.action_handler._stateless_actions[action_name]
                await action_callable(context, **kwargs)
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(tb)
                raise e
    elif action_name in app.ctx.action_handler._stateful_actions:
        calc_parts_callable, action_callable = app.ctx.action_handler._stateful_actions[
            action_name]
        parts = calc_parts_callable(None, **kwargs)

        # call_id = uuid4().hex
        call_id = "debugid"

        recv_conn, send_conn = [None] * parts, [None] * parts
        for i in range(parts):
            conn1, conn2 = Pipe(duplex=False)
            recv_conn[i] = conn1
            send_conn[i] = conn2

        # p = Process(target=_call_wrapper, args=(key, bucket, content_type,
        #                                         call_id, parts, action_name,
        #                                         action_callable, kwargs, send_conn))
        p = Thread(target=_call_wrapper, args=(key, bucket, content_type,
                                               call_id, parts, action_name,
                                               action_callable, kwargs, send_conn))
        p.daemon = True
        p.start()

        app.ctx.action_handler._current_actions[call_id] = {
            'parts': parts,
            'pipes': recv_conn,
            'process': p,
            'key': key,
            'bucket': bucket,
            'content_type': content_type
        }

        return json({'call_id': call_id, 'parts': parts})
    else:
        raise Exception(f"Unknown action {action_name}")
