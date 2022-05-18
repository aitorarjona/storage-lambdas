import io
import logging
import asyncio

logger = logging.getLogger(__name__)


class StreamResponseWrapper:
    def __init__(self, response):
        self.__response = response

    async def write(self, data):
        await self.__response.send(data)

    async def flush(self):
        await self.__response.eof()


class PipedWriter:
    def __init__(self, pipe):
        self.__pipe = pipe

    def write(self, data):
        chunk = bytes(data)
        if chunk:
            print('write', len(chunk), self.__pipe)
        self.__pipe.send(chunk)

    def flush(self):
        self.__pipe.send(b"")
    
    def close(self):
        self.flush()
        


class MultipartUploader:
    PART_SIZE = 64 * 1024 * 1024  # 64 MiB

    def __init__(self, s3client, bucket, key, content_type="application/octet-stream"):
        self.__buff = io.BytesIO()
        self.__part_count = 1
        self.__s3client = s3client
        self.__bucket = bucket
        self.__key = key
        self.__closed = False
        self.__parts = []
        self._content_type = content_type
        self.etag = None

    async def _setup(self):
        multipart_res = await self.__s3client.create_multipart_upload(
            Bucket=self.__bucket,
            Key=self.__key,
            ContentType=self._content_type
        )
        logger.debug(multipart_res)

        self.__upload_id = multipart_res['UploadId']

    def close(self):
        self.__closed = True

    async def write(self, data):
        if self.__closed:
            raise IOError()
        self.__buff.write(data)
        buff_sz = self.__buff.tell()
        # logger.debug(f'buff size is {buff_sz}')
        while buff_sz >= self.PART_SIZE:
            self.__buff.seek(0)
            chunk = self.__buff.read(self.PART_SIZE)
            upload_part_res = await self.__s3client.upload_part(
                Body=chunk,
                Bucket=self.__bucket,
                Key=self.__key,
                PartNumber=self.__part_count,
                UploadId=self.__upload_id
            )
            logger.debug(upload_part_res)
            self.__parts.append({
                'PartNumber': self.__part_count,
                'ETag': upload_part_res['ETag']
            })
            self.__part_count += 1
            rest = self.__buff.read(buff_sz - self.PART_SIZE)
            self.__buff = io.BytesIO()
            self.__buff.write(rest)
            buff_sz = self.__buff.tell()

    async def flush(self):
        logger.debug('flushing buffer')
        if self.__buff.tell() > 0:
            self.__buff.seek(0)
            chunk = self.__buff.read(self.PART_SIZE)
            logger.debug(f'put part of size {len(chunk)}')
            while len(chunk) > 0:
                upload_part_res = await self.__s3client.upload_part(
                    Body=chunk,
                    Bucket=self.__bucket,
                    Key=self.__key,
                    PartNumber=self.__part_count,
                    UploadId=self.__upload_id
                )
                logger.debug(upload_part_res)
                self.__parts.append({
                    'PartNumber': self.__part_count,
                    'ETag': upload_part_res['ETag']
                })
                self.__part_count += 1
                chunk = self.__buff.read(self.PART_SIZE)

        logger.debug(self.__parts)

        complete_multipart_response = await self.__s3client.complete_multipart_upload(
            Bucket=self.__bucket,
            Key=self.__key,
            UploadId=self.__upload_id,
            MultipartUpload={'Parts': self.__parts}
        )
        logger.debug(complete_multipart_response)

        self.etag = complete_multipart_response['ETag']

    async def _abort_upload(self):
        if self.__upload_id:
            logger.debug('aborting upload')
            abort_response = await self.__s3client.abort_multipart_upload(
                Bucket=self.__bucket,
                Key=self.__key,
                UploadId=self.__upload_id
            )
            logger.debug(abort_response)
