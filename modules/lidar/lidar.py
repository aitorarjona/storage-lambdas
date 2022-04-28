import traceback
import aiofiles
import asyncio
import secrets
import time
import logging

from storage_lambda_ric.handler import HandlerBase

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
            cmd=f'bin/lasindex -stdin -o {tmp_file_name}',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        info_proc = await asyncio.create_subprocess_shell(
            cmd=f'bin/lasinfo -stdin -no_check -no_vlrs -stdout',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            total = 0
            i = 0
            async for input_chunk in self.input_stream:
                total += len(input_chunk)
                # logger.debug(f'read chunk {i} of size {len(input_chunk)} (total is {total})')
                i += 1
                if not index_proc.stdin.is_closing():
                    index_proc.stdin.write(input_chunk)
                if not info_proc.stdin.is_closing():
                    info_proc.stdin.write(input_chunk)
                asyncio.create_task(self.output_stream.write(input_chunk))
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
        await self.output_stream.flush()

        logger.debug('puting meta to redis')
        async with aiofiles.open(tmp_file_name, 'rb') as f:
            index_data = await f.read()
            await self.redis_client.hset(self.full_key, 'las_index', index_data)
            for key, value in meta.items():
                await self.redis_client.hset(self.full_key, key, value)
        
        t1 = time.perf_counter()
        logger.debug(f'--- end extract_meta (total time: {t1 - t0}) ---')
    
    async def las2laz(self):
        logger.debug('--- start las2laz ---')
        t0 = time.perf_counter()

        proc = await asyncio.create_subprocess_shell(
            cmd='bin/laszip -stdin -stdout -olaz',
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

    async def filter_inside_XY(self, min_X, min_Y, max_X, max_Y):
        logger.debug('--- start filter_inside_XY ---')
        t0 = time.perf_counter()

        proc = await asyncio.create_subprocess_shell(
            cmd=f'bin/las2las -verbose -stdin -stdout -olas -inside {min_X} {min_Y} {max_X} {max_Y}',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def input_writer():
            input_chunk = await self.input_stream.read(65536)
            while input_chunk != b'':
                if not proc.stdin.is_closing():
                    proc.stdin.write(input_chunk)
                input_chunk = await self.input_stream.read(65536)
            if not proc.stdin.is_closing() and proc.stdin.can_write_eof():
                proc.stdin.write_eof()
            logger.debug('done writing input')

        async def output_reader():
            output_chunk = await proc.stdout.read()
            while output_chunk != b'':
                await self.output_stream.write(output_chunk)
                output_chunk = await proc.stdout.read()
            await self.output_stream.flush()
            logger.debug('done reading output')

        try:
            await asyncio.gather(input_writer(), output_reader())
        finally:
            out, err = await proc.communicate()
            logger.debug(out)
            logger.debug(err)

        # logger.debug('preprocessing ended')
        t1 = time.perf_counter()
        logger.debug(f'--- end filter_inside_XY --- (took {t1 - t0} s)')
