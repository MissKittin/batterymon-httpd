#!/usr/bin/env python3

import os
import sys
import ssl
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer

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
    routes_connect,
    wrap_http_handler,
    configure_ssl_context
)

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

    def _send_response(self, code, http_headers=None, string=None, add_content_length=True):
        http_headers=http_headers or {}
        self.send_response_only(code)

        if string is not None:
            if not isinstance(string, bytes):
                string=string.encode("utf-8")

            if add_content_length and "Content-Length" not in http_headers:
                http_headers["Content-Length"]=str(len(string))
        elif add_content_length and "Content-Length" not in http_headers:
            http_headers["Content-Length"]="0"

        for header_name, header_value in http_headers.items():
            self.send_header(header_name, header_value)

        self.end_headers()

        if string is not None:
            self.wfile.write(string)

    def _handle_method(self):
        method=self.command.lower()
        routes=self._ROUTES.get(method)

        if not routes:
            self._send_response(501)
            return

        for module in routes:
            handle_fn=getattr(module, "handle_"+method, None)

            if handle_fn and handle_fn(self, self.path, self._send_response):
                return

        if method == "get":
            return self._send_response(404)

        self._send_response(405)

    def version_string(self):
        return ""

    do_GET=do_POST=do_HEAD=do_PUT=do_DELETE=do_OPTIONS=do_PATCH=do_TRACE=do_CONNECT=_handle_method

if len(sys.argv) < 4:
    print("Usage:")
    print(" "+sys.argv[0]+" 8443 0.0.0.0 single|multi")
    print(" "+sys.argv[0]+" 8443 [::] single|multi")
    sys.exit(1)

if sys.argv[3] == "multi":
    class HTTPServerV4(ThreadingHTTPServer):
        pass

    class HTTPServerV6(ThreadingHTTPServer):
        address_family=socket.AF_INET6
else:
    class HTTPServerV4(HTTPServer):
        pass

    class HTTPServerV6(HTTPServer):
        address_family=socket.AF_INET6

if sys.argv[2].startswith("[") and sys.argv[2].endswith("]"):
    httpd=HTTPServerV6(
        (sys.argv[2][1:-1], int(sys.argv[1])),
        wrap_http_handler(SimpleHandler)
    )
else:
    httpd=HTTPServerV4(
        (sys.argv[2], int(sys.argv[1])),
        wrap_http_handler(SimpleHandler)
    )

if os.path.isdir(PROG_DIR+"/etc/ssl"):
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=PROG_DIR+"/etc/ssl/server.crt",
        keyfile=PROG_DIR+"/etc/ssl/server.key"
    )
    context.load_verify_locations(cafile=PROG_DIR+"/etc/ssl/ca.pem")
    context.verify_mode=ssl.CERT_REQUIRED

    configure_ssl_context(context)
    httpd.socket=context.wrap_socket(httpd.socket, server_side=True)
else:
    print("Notice: SSL disabled")

del PROG_DIR

httpd.serve_forever()
