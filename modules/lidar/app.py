import os
from pys3proxy.server import app

if __name__ == '__main__':
    target = os.environ.get('TARGET', '127.0.0.1:8000')
    host, port = target.split(':')
    app.run(host=host, port=int(port))