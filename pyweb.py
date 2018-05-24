#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author    : Yang
# Creadted  : 2017-04-18 22:12:09

import os
import re
import time
import json
import types
import urllib
import logging
import urlparse
import threading
import functools
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

ctx = threading.local()

HTTP_HEADERS = {'ALLOW': 'Allow', 'CONTENT-LANGUAGE': 'Content-Language', \
'PROXY-AUTHENTICATE': 'Proxy-Authenticate', 'AGE': 'Age', 'VARY': 'Vary', \
'LAST-MODIFIED': 'Last-Modified', 'LINK': 'Link', 'DATE': 'Date', \
'X-FRAME-OPTIONS': 'X-Frame-Options', 'SERVER': 'Server', \
'WWW-AUTHENTICATE': 'WWW-Authenticate', 'X-XSS-PROTECTION': 'X-XSS-Protection', \
'X-CONTENT-TYPE-OPTIONS': 'X-Content-Type-Options', 'X-POWERED-BY': 'X-Powered-By', \
'SET-COOKIE': 'Set-Cookie', 'EXPIRES': 'Expires', 'WARNING': 'Warning', \
'LOCATION': 'Location', 'X-FORWARDED-PROTO': 'X-Forwarded-Proto', \
'CONTENT-LOCATION': 'Content-Location', 'CONTENT-DISPOSITION': 'Content-Disposition', \
'CONTENT-ENCODING': 'Content-Encoding', 'TRANSFER-ENCODING': 'Transfer-Encoding', \
'ACCEPT-RANGES': 'Accept-Ranges', 'STRICT-TRANSPORT-SECURITY': 'Strict-Transport-Security', \
'REFRESH': 'Refresh', 'RETRY-AFTER': 'Retry-After', 'CONTENT-RANGE': 'Content-Range', \
'X-UA-COMPATIBLE': 'X-UA-Compatible', 'PRAGMA': 'Pragma', 'P3P': 'P3P', \
'CONTENT-TYPE': 'Content-Type', 'TRAILER': 'Trailer', 'CONTENT-LENGTH': 'Content-Length', \
'VIA': 'Via', 'CONTENT-MD5': 'Content-MD5', 'CONNECTION': 'Connection', 'ETAG': 'ETag', \
'CACHE-CONTROL': 'Cache-Control'}

HTTP_STATUSES = {
    # Informational
    100: 'Continue', 101: 'Switching Protocols', 102: 'Processing',
    # Successful
    200: 'OK', 201: 'Created', 202: 'Accepted', 203: 'Non-Authoritative Information',
    204: 'No Content', 205: 'Reset Content', 206: 'Partial Content',
    207: 'Multi Status', 226: 'IM Used',
    # Redirection
    300: 'Multiple Choices', 301: 'Moved Permanently', 302: 'Found', 303: 'See Other',
    304: 'Not Modified', 305: 'Use Proxy', 307: 'Temporary Redirect',
    # Client Error
    400: 'Bad Request', 401: 'Unauthorized', 402: 'Payment Required',
    403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed',
    406: 'Not Acceptable', 407: 'Proxy Authentication Required', 408: 'Request Timeout',
    409: 'Conflict', 410: 'Gone', 411: 'Length Required', 412: 'Precondition Failed',
    413: 'Request Entity Too Large', 414: 'Request URI Too Long', 415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable', 417: 'Expectation Failed', 418: "I'm a teapot",
    422: 'Unprocessable Entity', 423: 'Locked', 424: 'Failed Dependency', 426: 'Upgrade Required',
    # Server Error
    500: 'Internal Server Error', 501: 'Not Implemented', 502: 'Bad Gateway', 503: 'Service Unavailable',
    504: 'Gateway Timeout', 505: 'HTTP Version Not Supported', 507: 'Insufficient Storage', 510: 'Not Extended',
}

class HttpError(Exception):
    def __init__(self, code):
        self.status = "%s %s" % (code, HTTP_STATUSES[code])

    def __str__(self):
        return self.status

def notfound():
    return HttpError(404)

def badrequest():
    return HttpError(400)

def serverexcpet():
    return HttpError(500)

class Request(object):
    def __init__(self, environ):
        self._environ = environ

    @property
    def environ(self):
        return self._environ

    @property
    def request_method(self):
        return self._environ['REQUEST_METHOD']

    @property
    def query_string(self):
        return self._environ.get('QUERY_STRING', '')

    @property
    def path_info(self):
        return urllib.unquote(self._environ.get('PATH_INFO', ''))

    @property
    def input_stream(self):
        return self._environ['wsgi.input']

    def _get_headers(self):
        if not hasattr(self, '_headers'):
            hdrs = {}
            for k, v in self._environ.iteritems():
                if k.startswith('HTTP_'):
                    # convert 'HTTP_ACCEPT_ENCODING' to 'ACCEPT-ENCODING'
                    hdrs[k[5:].replace('_', '-').upper()] = v.decode('utf-8')
            self._headers = hdrs
        return self._headers

    @property
    def headers(self):
        return dict(**self._get_headers())

    def get_header(self, header, default=None):
        return self._get_headers().get(header.upper(), default)

    @property
    def params(self):
        if not hasattr(self, '_params'):
            pms = {}
            params_list = urlparse.parse_qsl(self.query_string, True)
            for k, v in params_list:
                v = urllib.unquote(v)
                pms[k] = v
            self._params = pms

        return self._params


class Response(object):
    def __init__(self):
        self._status = '200 OK'
        self._headers = {'CONTENT-TYPE': 'text/html; charset=utf-8'}

    @property
    def headers(self):
        return [(HTTP_HEADERS.get(k, k), v) for k, v in self._headers.iteritems()]

    def header(self, name):
        key = name.upper()
        if key not in HTTP_HEADERS:
            key = name
        return self._headers.get(key)

    def set_header(self, name, value):
        key = name.upper()
        if key not in HTTP_HEADERS:
            key = name
        self._headers[key] = str(value)

    def unset_header(self, name):
        key = name.upper()
        if key not in HTTP_HEADERS:
            key = name
        if key in HTTP_HEADERS:
            del self._headers[key]

    @property
    def content_type(self):
        return self.header('CONTENT-TYPE')

    @content_type.setter
    def content_type(self, value):
        if value:
            self.set_header('CONTENT-TYPE', value)
        else:
            self.unset_header('CONTENT-TYPE')

    @property
    def content_length(self):
        return self.header('CONTENT-LENGTH')

    @content_length.setter
    def content_length(self, value):
        if value:
            self.set_header('CONTENT-LENGTH', value)
        else:
            self.unset_header('CONTENT-LENGTH')

    @property
    def status_code(self):
        return int(self._status[:3])

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        value = int(value)
        if value not in HTTP_STATUSES:
            raise ValueError('Invalid http status value %s' % value)

        self._status = '%s %s' % (value, HTTP_STATUSES[value])

def get(path):
    def _decorator(func):
        func.__web_route__ = path
        func.__web_method__ = 'GET'
        return func
    return _decorator

def post(path):
    def _decorator(func):
        func.__web_route__ = path
        func.__web_method__ = 'POST'
        return func
    return _decorator

def put(path):
    def _decorator(func):
        func.__web_route__ = path
        func.__web_method__ = 'PUT'
        return func
    return _decorator

def jsonapi(func):
    @functools.wraps(func)
    def _wrapper(*args, **kargs):
        ret = json.dumps(func(*args, **kargs))
        ctx.response.content_type = 'application/json'
        return ret
    return _wrapper

_re_route = re.compile(r'(\:[a-zA-Z_]\w*)') # ':func_1' not ':1_func'

def _buildl_regex(path):
    r'''
    >>> _buildl_regex('/path/to:file')
    '^\\/path\\/to(?P<file>[^\\/]+)$'
    '''
    reg = StringIO()
    reg.write('^')
    is_var = False
    for v in _re_route.split(path):
        if is_var:
            var_name = v[1:] # ':func'
            reg.write(r'(?P<%s>[^\/]+)' % var_name)
        else:
            reg.write(re.escape(v))
        is_var = not is_var
    reg.write('$')
    return reg.getvalue()

class Route(object):
    def __init__(self, func):
        self.path = func.__web_route__
        self.method = func.__web_method__
        self.is_static = _re_route.search(self.path) is None
        if not self.is_static:
            self.route = re.compile(_buildl_regex(self.path))
        self.func = func
        self.params = None

    def match(self, path, method):
        if self.method != method:
            return False

        # dynamic with params
        if not self.is_static:
            m = self.route.match(path)
            if m:
                self.params = m.groups()
                return True

        # static no params
        if self.path == path:
            return True

        return False

    def process(self):
        if self.params:
            return self.func(*self.params)
        return self.func()

    def __str__(self):
        return 'Route(%s,%s,%s)' % ('dynamic' if not self.is_static else 'static', self.method, self.path)

    __repr__ = __str__

class WSGIApplication(object):
    def __init__(self):
        self._running = False
        self.routes = []

    def _load_module(self, mod):
        last_dot = mod.rfind('.')
        if last_dot == -1:
            return __import__(mod, globals(), locals())

        from_module = mod[:last_dot]
        import_module = mod[last_dot+1:]
        m = __import__(from_module, globals(), locals(), [import_module])
        return getattr(m, import_module)

    def add_module(self, mod):
        mod = mod if type(mod) == types.ModuleType else self._load_module(mod)
        for name in dir(mod):
            fn = getattr(mod, name)
            if callable(fn) and hasattr(fn, '__web_method__') and hasattr(fn, '__web_route__'):
                self.add_route(fn)

    def add_route(self, func):
        route = Route(func)
        self.routes.append(route)

    def get_route(self, request):
        assert isinstance(request, Request)
        for route in self.routes:
            if not route.match(request.path_info, request.request_method):
                continue
            return route
        raise notfound()

    def process(self, environ, start_response):
        try:
            tm = time.time()
            request = ctx.request = Request(environ)
            response = ctx.response = Response()
            ret = self.get_route(ctx.request).process()
            if isinstance(ret, unicode):
                ret = ret.encode('utf-8')
            if ret is None:
                ret = []
            cost = time.time() - tm
            logging.info("%s %s %s %s" % (request.request_method, response.status, request.path_info, cost))
            response.set_header("X-Cost", cost)
            start_response(response.status, response.headers)
            return ret
        except HttpError as e:
            start_response(e.status, response.headers)
            return ['<html><body><h1>', e.status, '</h1></body></html>']
        except Exception as e:
            logging.exception(e)
            start_response('500 Internal Server Error', [])
            return ['<html><body><h1>500 Internal Server Error</h1></body></html>']
        finally:
            del ctx.request 
            del ctx.response

    def run(self, port=10000, host='127.0.0.1'):
        from wsgiref.simple_server import make_server
        logging.info("server start %s:%s..." % (host, port))
        print("server start %s:%s..." % (host, port))
        server = make_server(host, port, self.process)
        server.serve_forever()
