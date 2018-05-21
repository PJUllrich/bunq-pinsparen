import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)

        content_length = int(self.headers['content-length'])
        post_body = self.rfile.read(content_length)

        if len(post_body) > 0:
            print(post_body)


def start_listening(port):
    print(f'Listening on localhost:{port}')
    server = HTTPServer(('', port), RequestHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
