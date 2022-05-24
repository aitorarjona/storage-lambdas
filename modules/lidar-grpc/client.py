from urllib import request
import grpc
import time
import argparse

from module_handler.rpc import module_service_pb2, module_service_pb2_grpc


def call_stateful_action(bucket, key, name, arguments, host='localhost', port=50051):
    with grpc.insecure_channel(f'{host}:{port}') as channel:
        stub = module_service_pb2_grpc.StorageLambdaModuleStub(channel)

        req = module_service_pb2.CallActionRequest(
            bucket=bucket,
            key=key,
            action_name=name,
            action_args=arguments,
            method=module_service_pb2.Method.GET)
        print(req)
        res = stub.CallStatefulAction(req)
        print(res)


def get_result(call_id, part_no, output_file, host='localhost', port=50051):
    with grpc.insecure_channel(f'{host}:{port}') as channel:
        stub = module_service_pb2_grpc.StorageLambdaModuleStub(channel)

        req = module_service_pb2.GetStatefulResultRequest(
            call_id=call_id,
            part=part_no
        )
        res = stub.GetStatefulActionResult(req)

        if output_file is not None:
            with open(output_file, 'wb') as out_f:
                for part in res:
                    print(f'Received chunk of size {len(part.chunk)}')
                    out_f.write(part.chunk)
        else:
            for part in res:
                print(f'Received chunk of size {len(part.chunk)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rpc', choices=['call_stateless', 'call_stateful', 'get_result'])
    parser.add_argument('--bucket', type=str)
    parser.add_argument('--key', type=str)
    parser.add_argument('--action', type=str)
    parser.add_argument('--argument', action='append', default=[], type=str)
    parser.add_argument('--call-id', type=str)
    parser.add_argument('--part-no', type=str)
    parser.add_argument('--input', type=str)
    parser.add_argument('--output', type=str)
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=50051)
    args = parser.parse_args()

    print(args)

    if args.rpc == 'call_stateful':
        action_arguments = {}
        if args.argument:
            for arg in args.argument:
                k, v = arg.split(':')
                action_arguments[k] = v

        call_stateful_action(
            bucket=args.bucket,
            key=args.key,
            name=args.action,
            arguments=action_arguments,
            host=args.host,
            port=args.port
        )
    elif args.rpc == 'get_result':
        assert args.call_id is not None
        assert args.part_no is not None
        get_result(
            call_id=args.call_id,
            part_no=int(args.part_no),
            output_file=args.output,
            host=args.host,
            port=args.port
        )



    # with grpc.insecure_channel('localhost:50051') as channel:
    #     stub = service_pb2_grpc.StorageLambdaServiceStub(channel)

    #     req = service_pb2.CallActionRequest(action_name='action_example', action_arguments={'arg1': 'val1'})
    #     res = stub.CallStatefulAction(req)
    #     print(res)

    #     time.sleep(3)

    #     def _do_get(args):
    #         call_id, part = args
    #         req = service_pb2.GetStatefulResultRequest(call_id=call_id, part=part)
    #         print(req)
    #         res = stub.GetStatefulActionResult(req)
    #         for message in res:
    #             print(message.chunk)

    #     with concurrent.futures.ThreadPoolExecutor() as pool:
    #         futures = []
    #         for part in range(res.parts):
    #             f = pool.submit(_do_get, (res.call_id, part))
    #             futures.append(f)
    #         [f.result() for f in futures]
