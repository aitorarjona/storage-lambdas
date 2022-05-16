from concurrent import futures
from multiprocessing import Pool, Process, Pipe
import logging
import time

import grpc

import service_pb2_grpc
import service_pb2


def my_action(action_context):
    print(action_context)
    time.sleep(6)
    for i in range(10):
        for pipe in action_context['pipes']:
            print('send', i, pipe)
            pipe.send(f"{i}".encode('utf-8'))

    for pipe in action_context['pipes']:
        pipe.send(b"")

    print('action done!')


class Server(service_pb2_grpc.StorageLambdaService):
    def __init__(self) -> None:
        super().__init__()
        self.__current_actions = {}

    def CallStatefulAction(self, request, context):
        print(request)

        callid = 'callid123456'
        parts = 4

        recv_conn, send_conn = [None] * parts, [None] * parts
        for i in range(parts):
            conn1, conn2 = Pipe(duplex=False)
            recv_conn[i] = conn1
            send_conn[i] = conn2
        self.__current_actions[callid] = recv_conn

        p = Process(target=my_action, args=({'pipes': send_conn},))
        p.start()

        return service_pb2.CallStatefulActionResponse(parts=parts, call_id=callid)

    def GetStatefulActionResult(self, request, context):
        print(self.__current_actions)
        print(request)
        action_context = self.__current_actions[request.call_id]

        pipe = action_context[request.part]
        chunk_data = pipe.recv()
        while chunk_data != b"":
            chunk_stub = service_pb2.GetStatefulResultResponse(chunk=chunk_data)
            yield chunk_stub
            chunk_data = pipe.recv()

        print('done for part', request.part)


def serve():
    target = '[::]:50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=80))
    service_pb2_grpc.add_StorageLambdaServiceServicer_to_server(Server(), server)
    server.add_insecure_port(target)
    logging.info("Start serving at %s", target)
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    serve()
