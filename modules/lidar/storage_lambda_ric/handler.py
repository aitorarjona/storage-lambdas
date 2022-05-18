from .routes import app
import logging


logger = logging.getLogger(__name__)


class Handler:
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
        app.ctx.action_handler = self
        app.run(host=self.host, port=self.port, verbosity=0)

    def stop(self):
        app.stop()
        for action_id, val in self._current_actions.values():
            logger.info('Kill background process for action %s', action_id)
            val['process'].terminate()
            val['process'].join()

