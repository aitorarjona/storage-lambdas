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
        app.run(host=self.host, port=self.port)


