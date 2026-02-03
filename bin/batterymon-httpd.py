#!/usr/bin/env python3

import os
import sys
import ssl
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

PROG_DIR=os.path.abspath(os.path.dirname(__file__)+"/..")

sys.path.insert(0, PROG_DIR)
from share import (
    routes_get,
    routes_post,
    routes_head,
    routes_put,
    routes_delete,
    routes_options,
    routes_patch,
    routes_trace,
    routes_connect
)

class HTTPServerV6(HTTPServer):
    address_family=socket.AF_INET6

class SimpleHandler(BaseHTTPRequestHandler):
    _ROUTES={
        "get": routes_get,
        "post": routes_post,
        "head": routes_head,
        "put": routes_put,
        "delete": routes_delete,
        "options": routes_options,
        "patch": routes_patch,
        "trace": routes_trace,
        "connect": routes_connect,
    }

    def _send_response(self, code, http_headers=None, string=None):
        self.send_response_only(code)

        if http_headers:
            for header_name, header_value in http_headers.items():
                self.send_header(header_name, header_value)

        if string is not None:
            if not isinstance(string, bytes):
                string=string.encode("utf-8")

            self.send_header("Content-Length", str(len(string)))
            self.end_headers()

            return self.wfile.write(string)

        self.send_header("Content-Length", "0")
        self.end_headers()

    def _handle_method(self):
        method=self.command.lower()
        routes=self._ROUTES.get(method)

        if not routes:
            self._send_response(501)
            return

        for module in routes:
            route_fn=getattr(module, "route_"+method, None)
            handle_fn=getattr(module, "handle_"+method, None)

            if route_fn and not route_fn(self, self.path):
                continue

            if handle_fn and handle_fn(self, self._send_response):
                return

        if method == "get":
            return self._send_response(404)

        self._send_response(405)

    def version_string(self):
        return ""

    do_GET=do_POST=do_HEAD=do_PUT=do_DELETE=do_OPTIONS=do_PATCH=do_TRACE=do_CONNECT=_handle_method

if len(sys.argv) < 3:
    print("Usage:")
    print(" "+sys.argv[0]+" 8443 0.0.0.0")
    print(" "+sys.argv[0]+" 8443 ::")
    sys.exit(1)

if sys.argv[2].startswith("[") and sys.argv[2].endswith("]"):
    httpd=HTTPServerV6(
        (sys.argv[2][1:-1], int(sys.argv[1])),
        SimpleHandler
    )
else:
    httpd=HTTPServer(
        (sys.argv[2], int(sys.argv[1])),
        SimpleHandler
    )

if os.path.isdir(PROG_DIR+"/etc/ssl"):
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=PROG_DIR+"/etc/ssl/server.crt",
        keyfile=PROG_DIR+"/etc/ssl/server.key"
    )
    context.load_verify_locations(cafile=PROG_DIR+"/etc/ssl/ca.pem")
    context.verify_mode=ssl.CERT_REQUIRED

    httpd.socket=context.wrap_socket(httpd.socket, server_side=True)
else:
    print("Notice: SSL disabled")

del PROG_DIR

httpd.serve_forever()
