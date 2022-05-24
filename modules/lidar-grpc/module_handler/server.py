from multiprocessing import Process, Pipe
from threading import Thread
import logging
import time
import os

import grpc

from .rpc import module_service_pb2, module_service_pb2_grpc
from .context import StatefulContext, StatelessContext, Method
from .streamwriter import BufferedPipeWriter

logger = logging.getLogger(__name__)


def _background_action_wrapper(key, bucket, content_type, call_id, parts,
                               action_name, action_args, action_callable,
                               method, send_conn):
    logger.debug('--- Background task for action %s (id=%s) started ---', action_name, call_id)

    output_streams = [os.fdopen(fd, 'wb') for fd in send_conn]

    action_context = StatefulContext(output_streams=output_streams,
                                     key=key,
                                     bucket=bucket,
                                     content_type=content_type,
                                     method=method)

    action_callable(action_context, **action_args)

    logger.debug('--- Background task for action %s (id=%s) '
                 'finished successfully ---', action_name, call_id)


class GRPCServer(module_service_pb2_grpc.StorageLambdaModule):
    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def CallStatefulAction(self, request, context):
        print(request)

        logger.info('---------> %s Stateful %s %s %s %s %s <---------', request.method, request.action_name,
                    request.action_args, request.bucket, request.key, request.content_type)

        calc_parts_callable, action_callable = self.handler._stateful_actions[request.action_name]

        action_context = StatelessContext(
            key=request.key,
            bucket=request.bucket,
            content_type=request.content_type,
            method=request.method
        )

        parts = calc_parts_callable(action_context, **request.action_args)

        call_id = 'debugid1234'

        recv_conn, send_conn = [None] * parts, [None] * parts
        # for i in range(parts):
        #     conn1, conn2 = Pipe(duplex=False)
        #     recv_conn[i] = conn1
        #     send_conn[i] = conn2
        
        for i in range(parts):
            rx, tx = os.pipe()
            recv_conn[i] = rx
            send_conn[i] = tx
        
        if request.method == 0:
            method = Method.GET
        elif request.method == 1:
            method = Method.PUT
        else:
            method = Method.GET

        process_args = (
            request.key, request.bucket, request.content_type, call_id, parts,
            request.action_name, request.action_args, action_callable,
            method, send_conn
        )
        p = Thread(target=_background_action_wrapper, args=process_args)
        p.daemon = True
        p.start()

        self.handler._current_actions[call_id] = {
            'parts': parts,
            'pipes': recv_conn,
            'process': p,
            'key': request.key,
            'bucket': request.bucket,
            'content_type': request.content_type
        }

        return module_service_pb2.CallStatefulActionResponse(parts=parts, call_id=call_id)

    def GetStatefulActionResult(self, request, context):
        print(request)
        print(self.handler._current_actions)
        action_context = self.handler._current_actions[request.call_id]

        fd = action_context['pipes'][request.part]
        pipe = os.fdopen(fd, 'rb')
        print('get part read')
        chunk_data = pipe.read(65536)
        print(f'going to send {len(chunk_data)}')
        while chunk_data != b"":
            chunk_stub = module_service_pb2.GetStatefulResultResponse(chunk=chunk_data)
            yield chunk_stub
            chunk_data = pipe.read(65536)
            print(f'going to send {len(chunk_data)}')

        print('done for part', request.part)
