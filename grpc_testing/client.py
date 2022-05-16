from xml.etree.ElementTree import QName


import grpc
import time

import concurrent.futures

import service_pb2
import service_pb2_grpc
    
if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.StorageLambdaServiceStub(channel)

        req = service_pb2.CallActionRequest(action_name='action_example', action_arguments={'arg1': 'val1'})
        res = stub.CallStatefulAction(req)
        print(res)

        time.sleep(3)

        def _do_get(args):
            call_id, part = args
            req = service_pb2.GetStatefulResultRequest(call_id=call_id, part=part)
            print(req)
            res = stub.GetStatefulActionResult(req)
            for message in res:
                print(message.chunk)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            futures = []
            for part in range(res.parts):
                f = pool.submit(_do_get, (res.call_id, part))
                futures.append(f)
            [f.result() for f in futures]
