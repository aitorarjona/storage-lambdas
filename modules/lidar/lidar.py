import traceback
import aiofiles
import asyncio
import secrets
import time
import os
import logging
import hashlib

import laspy
import numpy as np

from storage_lambda_ric.handler import Handler

logger = logging.getLogger(__name__)


async def extract_meta(context):
    logger.debug('--- start extract_meta ---')
    t0 = time.perf_counter()
    tmp_token = secrets.token_urlsafe(nbytes=4)
    tmp_file_name = f'/tmp/tmpindex-{tmp_token}.lax'

    index_proc = await asyncio.create_subprocess_shell(
        cmd=f'lasindex -stdin -o {tmp_file_name}',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    info_proc = await asyncio.create_subprocess_shell(
        cmd=f'lasinfo -stdin -no_check -no_vlrs -stdout',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        total = 0
        i = 0
        async for input_chunk in context.input_stream:
            total += len(input_chunk)
            # logger.debug(f'read chunk {i} of size {len(input_chunk)} (total is {total})')
            i += 1
            if not index_proc.stdin.is_closing():
                index_proc.stdin.write(input_chunk)
            if not info_proc.stdin.is_closing():
                info_proc.stdin.write(input_chunk)
            # asyncio.create_task(self.output_stream.write(input_chunk))
            await context.output_stream.write(input_chunk)
        if not index_proc.stdin.is_closing() and index_proc.stdin.can_write_eof():
            index_proc.stdin.write_eof()
        # if not index_proc.stdin.is_closing() and info_proc.stdin.can_write_eof():
        #     info_proc.stdin.write_eof()
        logger.debug('all input received')
    except RuntimeError as e:
        print(e)
        traceback.print_exc()
        raise e
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise e
    finally:
        logger.debug('joining child process')
        index_out, index_err = await index_proc.communicate()
        logger.debug('index output: %s %s', index_out.decode('utf-8'), index_err.decode('utf-8'))
        info_out, info_err = await info_proc.communicate()
        logger.debug('info output: %s %s', info_out.decode('utf-8'), info_err.decode('utf-8'))

    logger.debug('parsing output')
    first = True
    meta = {}
    for info_line in info_out.decode('utf-8').splitlines():
        if first:
            first = False
            continue
        line = info_line.strip()
        key, value = line.split(':')
        key = key.replace(' ', '_')
        value = value.replace('\'', '').strip().lstrip()
        meta[key] = value

    logger.debug('flushing writer stream')
    await context.output_stream.flush()

    logger.debug('puting meta to redis')
    async with aiofiles.open(tmp_file_name, 'rb') as f:
        index_data = await f.read()
        await context.redis_client.hset(context.full_key, 'las_index', index_data)
        for key, value in meta.items():
            await context.redis_client.hset(context.full_key, key, value)

    t1 = time.perf_counter()
    logger.debug(f'--- end extract_meta (total time: {t1 - t0}) ---')


async def las2laz(context):
    logger.debug('--- start las2laz ---')
    t0 = time.perf_counter()

    proc = await asyncio.create_subprocess_shell(
        cmd='laszip -stdin -stdout -olaz',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    total = 0
    async for i, input_chunk in enumerate(context.request.stream):
        total += len(input_chunk)
        logger.debug(f'read chunk {i} of size {len(input_chunk)} (total is {total})')
        proc.stdin.write(input_chunk)
        output_chunk = await proc.stdout.read(65536)
        await context.output_stream.write(output_chunk)
    logger.debug('all input received')

    logger.debug('processing rest of output')
    output_chunk = await proc.stdout.read(65536)
    while output_chunk != b'':
        await context.output_stream.write(output_chunk)
        output_chunk = await proc.stdout.read(65536)
    logger.debug('all output sent')

    logger.debug('joining child process')
    out, err = await proc.communicate()
    if out:
        await context.output_stream.write(out)
    logger.debug(err)

    logger.debug('flushing writer stream')
    await context.output_stream.flush()

    t1 = time.perf_counter()
    logger.debug(f'--- end las2laz (total time: {t1 - t0}) ---')


async def filter_inside_XY(context, min_X, min_Y, max_X, max_Y):
    logger.debug('--- start filter_inside_XY ---')
    t0 = time.perf_counter()

    key = hashlib.md5(context.full_key.encode('utf-8')).hexdigest()
    tmp_file_name = f'/tmp/{key}'

    if index_data := await context.redis_client.hget(context.full_key, 'las_index'):
        logger.debug('using las index')

        if not os.path.exists(tmp_file_name + '.lax'):
            logger.debug('index not found in cache, getting from redis...')
            async with aiofiles.open(tmp_file_name + '.lax', 'wb') as f:
                await f.write(index_data)

        try:
            lock = context.redis_client.lock(context.full_key + '.lock')
            logger.debug('acquiring lock...')
            await lock.acquire()
            if not os.path.exists(tmp_file_name + '.las'):
                logger.debug('lock acquired')
                logger.debug('data not found in cache, getting from stream...')
                await context.do_get()
                async with aiofiles.open(tmp_file_name + '.las', 'wb') as f:
                    input_chunk = await context.input_stream.read(65536)
                    while input_chunk != b'':
                        await f.write(input_chunk)
                        input_chunk = await context.input_stream.read(65536)
        finally:
            logger.debug('releasing lock...')
            await lock.release()

        cmd = f'las2las -verbose -i {tmp_file_name}.las -stdout -olas -inside {min_X} {min_Y} {max_X} {max_Y}'
        proc = await asyncio.create_subprocess_shell(
            cmd=cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            output_chunk = await proc.stdout.read()
            while output_chunk != b'':
                await context.output_stream.write(output_chunk)
                output_chunk = await proc.stdout.read()
            await context.output_stream.flush()
            logger.debug('done reading output')
        finally:
            logger.debug('joining child process')
            out, err = await proc.communicate()
            logger.debug(out)
            logger.debug(err)

        # os.remove(tmp_file_name + '.las')
        # os.remove(tmp_file_name + '.lax')
    else:
        logger.debug('index not found - reading all points')

        proc = await asyncio.create_subprocess_shell(
            cmd=f'las2las -verbose -stdin -stdout -olas -inside {min_X} {min_Y} {max_X} {max_Y}',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def input_writer():
            input_chunk = await context.input_stream.read(65536)
            while input_chunk != b'':
                if not proc.stdin.is_closing():
                    proc.stdin.write(input_chunk)
                input_chunk = await context.input_stream.read(65536)
            if not proc.stdin.is_closing() and proc.stdin.can_write_eof():
                proc.stdin.write_eof()
            logger.debug('done writing input')

        async def output_reader():
            output_chunk = await proc.stdout.read()
            while output_chunk != b'':
                await context.output_stream.write(output_chunk)
                output_chunk = await proc.stdout.read()
            await context.output_stream.flush()
            logger.debug('done reading output')

        try:
            await asyncio.gather(input_writer(), output_reader())
        finally:
            out, err = await proc.communicate()
            logger.debug(out)
            logger.debug(err)

    t1 = time.perf_counter()
    logger.debug(f'--- end filter_inside_XY --- (took {t1 - t0} s)')


async def tiled_partition(context, parts):
    logger.debug(f'--- start tiled_partition ---')
    t0 = time.perf_counter()

    parts = int(parts)

    s3client = context.get_sync_s3client()
    res = s3client.get_object(Bucket=context.bucket, Key=context.key)
    reader = res['Body']

    las_input = laspy.lasreader.LasReader(source=reader)
    x_min, y_min = las_input.header.x_min, las_input.header.y_min
    x_max, y_max = las_input.header.x_max, las_input.header.y_max

    x_size = (x_max - x_min) / parts
    y_size = (y_max - y_min) / parts

    sub_bounds = []
    for i in range(parts):
        for j in range(parts):
            x_min_bound = (x_size * i) + x_min
            y_min_bound = (y_size * j) + y_min
            x_max_bound = x_min_bound + x_size
            y_max_bound = y_min_bound + y_size
            sub_bounds.append((x_min_bound, y_min_bound, x_max_bound, y_max_bound))

    output_writers = [laspy.laswriter.LasWriter(dest=stream, header=las_input.header)
                      for stream in context.output_streams]
    print(sub_bounds)

    try:
        count = 0
        for points in las_input.chunk_iterator(1_000_000):
            x, y = points.x.copy(), points.y.copy()
            point_piped = 0

            for i, (x_min, y_min, x_max, y_max) in enumerate(sub_bounds):
                mask = (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)

                if np.any(mask):
                    sub_points = points[mask]
                    print('writing points')
                    output_writers[i].write_points(sub_points)

                point_piped += np.sum(mask)
                if point_piped == len(points):
                    break
            count += len(points)
            print(f"{count / las_input.header.point_count * 100}%")
    finally:
        for writer in context.output_streams:
            writer.close()
        las_input.close()

    t1 = time.perf_counter()
    logger.debug(f'--- end tiled_partition --- (took {t1 - t0} s)')


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', logging.INFO))
    logging.getLogger('botocore').setLevel(logging.CRITICAL)

    target = os.environ.get('TARGET', '127.0.0.1:8000')
    logging.info('Listening on %s', target)
    host, port = target.split(':')

    lidar_handler = Handler(host=host, port=int(port))

    lidar_handler.stateless_action('extract_meta', extract_meta)
    lidar_handler.stateless_action('las2laz', las2laz)
    lidar_handler.stateless_action('filter_inside_XY', filter_inside_XY)

    lidar_handler.stateful_action('tiled_partition', action_callable=tiled_partition,
                                  calc_parts_callable=lambda _, parts: int(parts))

    try:
        lidar_handler.serve()
    except KeyboardInterrupt:
        print('killing server')
        lidar_handler.stop()
