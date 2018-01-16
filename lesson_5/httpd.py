#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Веб‑сервер должен уметь:
    Масштабироваться на несколько worker'ов
    Числов worker'ов задается аргументом командной строки ‑w
    Отвечать 200 или 404 на GET‑запросы и HEAD‑запросы
    Отвечать 405 на прочие запросы
    Возвращать файлы по произвольному пути в DOCUMENT_ROOT.
    Вызов /file.html должен возвращать содердимое DOCUMENT_ROOT/file.html
    DOCUMENT_ROOT задается аргументом командной строки ‑r
    Возвращать index.html как индекс директории
    Вызов /directory/ должен возвращать DOCUMENT_ROOT/directory/index.html
    Отвечать следующими заголовками для успешных GET‑запросов: Date, Server, Content‑Length, Content‑
    Type, Connection
    Корректный Content‑Type для: .html, .css, .js, .jpg, .jpeg, .png, .gif, .swf
    Понимать пробелы и %XX в именах файлов
"""

"""
REQUEST:

    GET /tutorials/other/top-20-mysql-best-practices/ HTTP/1.1
    Host: net.tutsplus.com
    User-Agent: Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5 (.NET CLR 3.5.30729)
    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
    Accept-Language: en-us,en;q=0.5
    Accept-Encoding: gzip,deflate
    Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7
    Keep-Alive: 300
    Connection: keep-alive
    Cookie: PHPSESSID=r2t5uvjq435r4q7ib3vtdjq120
    Pragma: no-cache
    Cache-Control: no-cache
"""

"""
RESPONSE:

    HTTP/1.x 200 OK
    Transfer-Encoding: chunked
    Date: Sat, 28 Nov 2009 04:36:25 GMT
    Server: LiteSpeed
    Connection: close
    X-Powered-By: W3 Total Cache/0.8
    Pragma: public
    Expires: Sat, 28 Nov 2009 05:36:25 GMT
    Etag: "pub1259380237;gz"
    Cache-Control: max-age=3600, public
    Content-Type: text/html; charset=UTF-8
    Last-Modified: Sat, 28 Nov 2009 03:50:37 GMT
    X-Pingback: http://net.tutsplus.com/xmlrpc.php
    Content-Encoding: gzip
    Vary: Accept-Encoding, Cookie, User-Agent
"""

import sys
import socket
import select
import errno
import threading
import time


class MyTCPServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5
    allow_reuse_address = False
    # timeout = None
    daemon_threads = False

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.__is_shut_down = threading.Event()
        self.__shutdown_request = False
        self.socket = socket.socket(self.address_family, self.socket_type)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

    def serve_forever(self, poll_interval=0.5):
        """
            Handle one request at a time until shutdown.
            Polls for shutdown every poll_interval seconds.
        """
        logging.info('Server forever')
        self.__is_shut_down.clear()
        try:
            while not self.__shutdown_request:
                readable, writable, exceptional = select.select([self], [], [], poll_interval)
                if self in readable:
                    self._handle_request_noblock()
        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()

    def shutdown(self):
        """Stops the serve_forever loop.

        Blocks until the loop has finished. This must be called while
        serve_forever() is running in another thread, or it will
        deadlock.
        """
        self.__shutdown_request = True
        self.__is_shut_down.wait()

    def server_bind(self):
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

    def server_activate(self):
        logging.info('server_activate')
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        self.socket.close()

    def fileno(self):
        return self.socket.fileno()

    def get_request(self):
        return self.socket.accept()

    def process_request_thread(self, request, client_address):
        logging.info('process_request_thread in port: ' + str(client_address[1]))
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        logging.info('process request threading in port: ' + str(client_address[1]))
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
        t.daemon = self.daemon_threads
        t.start()

    def shutdown_request(self, request):
        logging.info('shutdown_request')
        """Called to shutdown and close an individual request."""
        try:
            #explicitly shutdown.  socket.close() merely releases
            #the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
        except socket.error:
            pass #some platforms may raise ENOTCONN here
        self.close_request(request)

    def close_request(self, request):
        """Called to clean up an individual request."""
        logging.info('close_request')
        logging.info('*'*100)
        request.close()

    def finish_request(self, request, client_address):
        logging.info('finish_request')
        logging.info(request)
        logging.info(client_address)
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, self)

    def _handle_request_noblock(self):
        logging.info('-'*100)
        logging.info('_handle_request_noblock')
        try:
            request, client_address = self.get_request()
            logging.info(client_address)
        except socket.error:
            return
        try:
            self.process_request(request, client_address)
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def handle_error(self, request, client_address):
        print '-'*40
        print 'Exception happened during processing of request from',
        print client_address
        import traceback
        traceback.print_exc() # XXX But this goes to stderr!
        print '-'*40


tmpl = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Response</title>
    </head>
    <body>
        <h1>Response</h1>
        <p>Message: %(message)s.</p>
    </body>
</html>
"""


class ThreadedRequestHandler(object):

    sys_version = "Python/" + sys.version.split()[0]
    server_version = "MyHTTPServer"
    default_request_version = "HTTP/0.9"
    request_version = ''
    protocol_version = "HTTP/1.0"
    responses = {
        '200': 'OK',
        '500': 'Server Error'
    }

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    def parse_request(self):
        return

    def version_string(self):
        """Return the server software version string."""
        return self.server_version + ' ' + self.sys_version

    def send_response(self, code, message=None):
        """Send the response header only."""
        if self.request_version != 'HTTP/0.9':
            if message is None:
                if code in self.responses:
                    message = self.responses[code][0]
                else:
                    message = ''
            if not hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(("%s %d %s\r\n" %
                    (self.protocol_version, code, message)).encode(
                        'latin-1', 'strict'))
        self.send_header('Server', self.version_string())

    def send_header(self, keyword, value):
        """Send a MIME header to the headers buffer."""
        if self.request_version != 'HTTP/0.9':
            if not hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(
                ("%s: %s\r\n" % (keyword, value)).encode('latin-1', 'strict'))

        if keyword.lower() == 'connection':
            if value.lower() == 'close':
                self.close_connection = True
            elif value.lower() == 'keep-alive':
                self.close_connection = False

    def handle(self):
        logging.info('Handle request')
        data = self.request.recv(1024).split('\r\n')
        logging.info('request  :' + data[0])
        method, url, http_type = data[0].split(' ')
        cur_thread = threading.current_thread()
        self.send_response(200, message='OK')
        self.send_header("Content-type", 'text/html;')
        self.send_header("Content-Length", '')
        response = ''.join(self._headers_buffer)
        response = response + tmpl % {'message': cur_thread.name}
        # print 'response', response
        self.request.sendall(response)

    def setup(self):
        pass

    def finish(self):
        pass


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        filename=None,
        format='[%(asctime)s] %(levelname)s %(message)s',
        datefmt='%H:%M:%S %d-%b-%Y',
        level=logging.DEBUG
    )

    HOST, PORT = "0.0.0.0", 9990

    server = MyTCPServer((HOST, PORT), ThreadedRequestHandler)

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True

    try:
        server_thread.start()
        logging.info("Server started at {} port {}".format(HOST, PORT))
        while True: time.sleep(100)
    except (KeyboardInterrupt, SystemExit):
        server.shutdown()
        server.server_close()
        exit()
