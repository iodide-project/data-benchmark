import atexit
import http
import http.server
import multiprocessing
import os
import queue
import socketserver
import sys


import generate


def spawn_web_server(path):
    global PORT

    print("Spawning webserver...")

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=run_web_server, args=(path, q,))

    def shutdown_webserver():
        q.put("TERMINATE")
        p.join()
    atexit.register(shutdown_webserver)

    p.start()
    return q.get()


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        attrs = {}
        path = self.translate_path(self.path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(http.HTTPStatus.NOT_FOUND, "File not found")
            return None

        if self.path.endswith('.html'):
            mimetype = 'text/html'
        elif self.path.endswith('.js'):
            mimetype = 'application/javascript'
        else:
            filename = os.path.basename(path)
            attrs = generate.get_attrs_for_file(filename)

            if attrs['format'] == 'csv':
                mimetype = 'text/csv'
            elif attrs['format'] == 'json':
                mimetype = 'application/json'
            else:
                raise NotImplementedError()

        fs = os.fstat(f.fileno())

        self.send_response(http.HTTPStatus.OK)
        self.send_header('Content-type', mimetype)
        self.send_header('Content-Length', str(fs.st_size))
        if attrs.get('compression') == 'gzip':
            self.send_header('Content-Encoding', 'gzip')
        # We don't ever want the browser to cache
        self.send_header('pragma', 'no-cache')
        self.send_header('cache-control', 'no-cache')
        self.end_headers()

        return f


def run_web_server(path, q):
    print("Running webserver...", path)

    os.chdir(path)
    Handler = CustomHTTPRequestHandler

    def dummy_log(*args, **kwargs):
        pass
    Handler.log_message = dummy_log

    with socketserver.TCPServer(("", 0), Handler) as httpd:
        host, port = httpd.server_address
        print(f"Serving {path} on port {port}")
        q.put(port)

        def service_actions():
            try:
                if q.get(False) == "TERMINATE":
                    sys.exit(0)
                    httpd.shutdown()
            except queue.Empty:
                pass

        httpd.service_actions = service_actions
        httpd.serve_forever()
