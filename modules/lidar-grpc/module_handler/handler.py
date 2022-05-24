import logging
from concurrent import futures

import grpc

from .server import GRPCServer
from .rpc import module_service_pb2_grpc

logger = logging.getLogger(__name__)


class ModuleHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._stateless_actions = {}
        self._stateful_actions = {}
        self._current_actions = {}

    def stateless_action(self, name, action_callable):
        self._stateless_actions[name] = action_callable

    def stateful_action(self, name, action_callable, calc_parts_callable):
        self._stateful_actions[name] = calc_parts_callable, action_callable

    def serve(self):
        self.__server = grpc.server(futures.ThreadPoolExecutor(max_workers=80))
        module_service_pb2_grpc.add_StorageLambdaModuleServicer_to_server(GRPCServer(handler=self), self.__server)
        self.__server.add_insecure_port(f'{self.host}:{self.port}')
        self.__server.start()
        self.__server.wait_for_termination()

    def stop(self):
        logger.debug('Stopping service')
        self.__server.stop(grace=5)
        logger.debug(self._current_actions)
        for action_id, val in self._current_actions.items():
            logger.info('Kill background process for action %s', action_id)
            if hasattr(val['process'], 'terminate'):
                val['process'].terminate()
            elif hasattr(val['process'], 'kill'):
                val['process'].kill()
            val['process'].join()
        logger.info('Bye!')

