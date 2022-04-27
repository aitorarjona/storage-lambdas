import aiofiles
import asyncio
import secrets
import time
import logging

from pys3proxy.handler import HandlerBase

logger = logging.getLogger(__name__)


class LASModule(HandlerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def extract_meta(self):
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

        total = 0
        async for i, input_chunk in enumerate(self.request.stream):
            total += len(input_chunk)
            logger.debug(f'read chunk {i} of size {len(input_chunk)} (total is {total})')
            index_proc.stdin.write(input_chunk)
            info_proc.stdin.write(input_chunk)
            await self.output_stream.write(input_chunk)
        logger.debug('all input received')

        logger.debug('joining child process')
        index_out, index_err = await index_proc.communicate()
        logger.debug('index output: %s %s', index_out.decode('utf-8'), index_err.decode('utf-8'))
        info_out, info_err = await info_proc.communicate()
        logger.debug('info output: %s %s', info_out.decode('utf-8'), info_err.decode('utf-8'))

        logger.debug('parsing output')
        first = True
        meta = {}
        for info_line in info_out.splitlines():
            if first:
                first = False
                continue
            line = info_line.strip()
            key, value = line.split(':')
            key = key.replace(' ', '_')
            value = value.strip().lstrip()
            meta[key] = value

        logger.debug('flushing writer stream')
        await self.output_stream.flush()

        logger.debug('puting meta to redis')
        async with aiofiles.open(tmp_file_name, 'rb') as f:
            index_data = await f.read()
            await self.redis_client.hset(self.object_key, 'index', index_data)
            for key, value in meta.items():
                await self.redis_client.hset(self.object_key, key, value)
        
        t1 = time.perf_counter()
        logger.debug(f'--- end extract_meta (total time: {t1 - t0}) ---')
    
    async def las2laz(self):
        logger.debug('--- start las2laz ---')
        t0 = time.perf_counter()

        proc = await asyncio.create_subprocess_shell(
            cmd='laszip -stdin -stdout -olaz',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        total = 0
        async for i, input_chunk in enumerate(self.request.stream):
            total += len(input_chunk)
            logger.debug(f'read chunk {i} of size {len(input_chunk)} (total is {total})')
            proc.stdin.write(input_chunk)
            output_chunk = await proc.stdout.read(65536)
            await self.output_stream.write(output_chunk)
        logger.debug('all input received')

        logger.debug('processing rest of output')
        output_chunk = await proc.stdout.read(65536)
        while output_chunk != b'':
            await self.output_stream.write(output_chunk)
            output_chunk = await proc.stdout.read(65536)
        logger.debug('all output sent')

        logger.debug('joining child process')
        out, err = await proc.communicate()
        if out:
            await self.output_stream.write(out)
        logger.debug(err)

        logger.debug('flushing writer stream')
        await self.output_stream.flush()

        t1 = time.perf_counter()
        logger.debug(f'--- end las2laz (total time: {t1 - t0}) ---')

    async def getXY(self, min_X, min_Y, max_X, max_Y):
        logger.debug('--- start getXY ---')
        t0 = time.perf_counter()

        proc = await asyncio.create_subprocess_shell(
            cmd=f'las2las -verbose -stdin -stdout -olas -inside {min_X} {min_Y} {max_X} {max_Y}',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def input_writer():
            input_chunk = await self.input_stream.read(65536)
            while input_chunk != b'':
                proc.stdin.write(input_chunk)
                input_chunk = await self.input_stream.read(65536)
            logger.debug('done writing input')

        async def output_reader():
            output_chunk = await proc.stdout.read()
            while output_chunk != b'':
                await self.response.send(output_chunk)
                output_chunk = await proc.stdout.read()
            logger.debug('done reading output')

        try:
            await asyncio.gather(input_writer(), output_reader())
        finally:
            out, err = await proc.communicate()
            logger.debug(out)
            logger.debug(err)

        # logger.debug('preprocessing ended')
        t1 = time.perf_counter()
        logger.debug(f'--- end getXY --- (took {t1 - t0} s)')
