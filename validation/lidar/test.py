import os
import laspy
import time
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib3
from urllib.parse import urlencode

N_SPLIT_SQUARE = 2
DATA_BUCKET = 'lidarbucket'
KEY = 'PNOA_2016_CAT_322-324-4568-4570_ORT-CLA-COL.las'
S3_ACCESS_KEY_ID = 'minio'
S3_SECRET_ACCESS_KEY = 'miniostorage'
S3_ENDPOINT = 'http://127.0.0.1:8080'
# S3_ENDPOINT = 'http://192.168.1.144:9000'
REGION = 'us-east-1'


def square_split(x_min, y_min, x_max, y_max, square_splits):
    x_size = (x_max - x_min) / square_splits
    y_size = (y_max - y_min) / square_splits

    bounds = []
    for i in range(square_splits):
        for j in range(square_splits):
            x_min_bound = (x_size * i) + x_min
            y_min_bound = (y_size * j) + y_min
            x_max_bound = x_min_bound + x_size
            y_max_bound = y_min_bound + y_size
            bounds.append((x_min_bound, y_min_bound, x_max_bound, y_max_bound))
    return bounds


def get_object_query(bucket, key, query=None, query_args=None):
    session = boto3.Session(
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY
    )
    credentials = session.get_credentials()
    creds = credentials.get_frozen_credentials()

    url = os.path.join(S3_ENDPOINT, bucket, key)

    fields = {}
    if query:
        fields['action'] = query
        if query_args:
            for k, v in query_args.items():
                fields[k] = v

    print('GET %s %s', url, str(fields))

    request = AWSRequest(method='GET', url=url, data=None, params=fields, headers=None)
    SigV4Auth(creds, "s3", REGION).add_auth(request)
    signed_headers = dict(request.headers)

    http = urllib3.PoolManager()

    t0 = time.perf_counter()
    res = http.request('GET', url, fields=fields, headers=signed_headers, retries=False, preload_content=False)
    t1 = time.perf_counter()

    if res.status not in (200,):
        body = res.data
        print(res.status)
        print(dict(res.headers))
        # print(body)
        raise Exception()

    elapsed = t1 - t0
    print(elapsed)
    print(res.status)

    return res.stream()


def put_object_query(bucket, key, body, query=None, query_args=None):
    session = boto3.Session(
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY
    )
    credentials = session.get_credentials()
    creds = credentials.get_frozen_credentials()

    base_url = os.path.join(S3_ENDPOINT, bucket, key)

    fields = {}
    if query:
        fields['action'] = query
        if query_args:
            for k, v in query_args.items():
                fields[k] = v

    encoded_args = urlencode(fields)
    full_url = base_url + "?" + encoded_args

    print(f'PUT {base_url} {fields}')

    if isinstance(body, str):
        file_path = body
        content_len = os.stat(file_path).st_size
        with open(file_path, 'rb') as file_body:
            stream_body = iter(lambda: file_body.read(65536), b'')
            request = AWSRequest(method='PUT', url=base_url, data=None, params=fields, headers={'x-amz-content-sha256': 'STREAMING-AWS4-HMAC-SHA256-PAYLOAD'})
            SigV4Auth(creds, "s3", REGION).add_auth(request)
            signed_headers = dict(request.headers)
            signed_headers['Content-Length'] = content_len
            signed_headers['Content-Type'] = "application/vnd.las"
            
            http = urllib3.PoolManager()
            
            t0 = time.perf_counter()
            res = http.request('PUT', full_url, body=stream_body, headers=signed_headers, retries=False, preload_content=False)
            t1 = time.perf_counter()
    else:
        request = AWSRequest(method='PUT', url=base_url, data=body, params=fields, headers=None)
        SigV4Auth(creds, "s3", REGION).add_auth(request)
        signed_headers = dict(request.headers)
        signed_headers['Content-Length'] = len(body)
        signed_headers['Content-Type'] = "application/vnd.las"
            
        http = urllib3.PoolManager()

        t0 = time.perf_counter()
        res = http.request('PUT', full_url, body=stream_body, headers=signed_headers, retries=False, preload_content=False)
        t1 = time.perf_counter()
        pass

    elapsed = t1 - t0
    print(elapsed)
    print(res.status)
    print(dict(res.headers))
    print(res.data)

    return res.data


def get_chunks():
    las_input = laspy.open('/media/aitor/USBSSD/lidar-prades/las/prades-merged/PNOA_2016_CAT_322-324-4568-4570_ORT-CLA-COL.las', mode='r')
    x_min, y_min = las_input.header.x_min, las_input.header.y_min
    x_max, y_max = las_input.header.x_max, las_input.header.y_max
    sub_bounds = square_split(x_min, y_min, x_max, y_max, N_SPLIT_SQUARE)

    for i, sub_bound in enumerate(sub_bounds):
        min_X, min_Y, max_X, max_Y = sub_bound
        args = {'min_X': min_X, 'min_Y': min_Y, 'max_X': max_X, 'max_Y': max_Y}
        stream = get_object_query(bucket=DATA_BUCKET, key=KEY, query='filter_inside_XY', query_args=args)
        input_file_path = os.path.join('/tmp', f'chunk{i}.las')
        with open(input_file_path, 'wb') as file:
            for chunk in stream:
                file.write(chunk)


def extract_meta_get():
    stream = get_object_query(bucket=DATA_BUCKET, key=KEY, query='extract_meta', query_args={})
    result = b''.join(stream)
    # print(result.decode('utf-8'))
    print(len(result))

def extract_meta_put(file):
    put_object_query(bucket=DATA_BUCKET, key=KEY, body=file, query='extract_meta', query_args={})

    


if __name__ == '__main__':
    # extract_meta()
    extract_meta_put(file='/media/aitor/USBSSD/lidar-prades/las/prades-merged/PNOA_2016_CAT_322-324-4568-4570_ORT-CLA-COL.las')
    # get_chunks()



