import os
import logging
from pys3proxy.server import app

if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', logging.INFO))
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    target = os.environ.get('TARGET', '127.0.0.1:8000')
    logging.info('Listening on %s', target)
    host, port = target.split(':')
    app.run(host=host, port=int(port))