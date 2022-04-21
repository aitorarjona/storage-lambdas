import aiofiles
import asyncio
import secrets
import time
import logging

logger = logging.getLogger(__name__)


class LASModule:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def preprocess(self):
        logger.debug('starting preprocessing')
        t0 = time.perf_counter()
        tmp_token = secrets.token_urlsafe(nbytes=4)
        tmp_file_name = f'/tmp/tmpindex-{tmp_token}.lax'

        index_proc = await asyncio.create_subprocess_shell(
            cmd=f'bin/lasindex -stdin -o {tmp_file_name}',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        compress_proc = await asyncio.create_subprocess_shell(
            cmd='bin/laszip -stdin -stdout -olaz',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        i = 0
        acum = 0
        async for input_chunk in self.request.stream:
            acum += len(input_chunk)
            # logger.debug(f'{i}: read chunk of size {len(input_chunk)}, acum {acum}')
            i += 1
            index_proc.stdin.write(input_chunk)
            compress_proc.stdin.write(input_chunk)
            output_chunk = await compress_proc.stdout.read(65536)
            await self.output_stream.write(output_chunk)
        logger.debug('all input received')

        logger.debug('processing rest of output')
        output_chunk = await compress_proc.stdout.read(65536)
        while output_chunk != b'':
            await self.output_stream.write(output_chunk)
            output_chunk = await compress_proc.stdout.read(65536)
        logger.debug('all output sent')

        logger.debug('joining child processes')
        out, err = await compress_proc.communicate()
        if out:
            await self.output_stream.write(out)
        logger.debug(err)

        out, err = await index_proc.communicate()
        logger.debug(out, err)
        logger.debug('child processes ended')

        logger.debug('flushing writer stream')
        await self.output_stream.flush()
        logger.debug('ok')

        logger.debug('puting index to redis')
        async with aiofiles.open(tmp_file_name, 'rb') as f:
            index_data = await f.read()
            await self.redis_client.set('salou-index', index_data)

        logger.debug('preprocessing ended')
        t1 = time.perf_counter()
        logger.debug(f'total time: {t1 - t0}')

    async def getXY(self, min_X, min_Y, max_X, max_Y):
        logger.debug('--- start getXY ---')
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
                proc.stdin.write(input_chunk)
                input_chunk = await self.input_stream.read(65536)
            logger.debug('done writing input')

        async def output_reader():
            output_chunk = await proc.stdout.read()
            while output_chunk != b'':
                await self.response.send(output_chunk)
                output_chunk = await proc.stdout.read()
            logger.debug('done reading output')

        await asyncio.gather(input_writer(), output_reader())

        out, err = await proc.communicate()
        logger.debug(out)
        logger.debug(err)

        logger.debug('preprocessing ended')
        t1 = time.perf_counter()
        logger.debug(f'--- end getXY --- (took {t1 - t0} s)')
