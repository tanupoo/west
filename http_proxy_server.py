#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import traceback    # for debug
import uuid
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from chunkable_http_server import ChunkableHTTPRequestHandler
from inet_string import inet_string
from threading import currentThread, Event
import time
from debug_tools import is_debug, debug_print

'''
HTTP Proxy Handler
'''
class ProxyHandler(ChunkableHTTPRequestHandler):

    server_response_timer = 5
    waiting_for_server = None

    def do_GET(self):
        if not self.pre_process():
            return
        self.read_content()

    def do_POST(self):
        if not self.pre_process():
            return
        self.read_content()

    def pre_process(self):
        '''
        it called just immediately after the 1st line of a request is ready to
        be read.
        '''
        #
        if is_debug(1, self.server.west):
            print('DEBUG:', self.__class__, currentThread().getName())
        print('INFO: an http client connected from %s, request %s %s' %
              (repr(self.client_address), self.command, self.path))
        #
        # check whether there is a socket for the peer.
        # it it checked again later.
        #
        if not self.server.s_ws:
            print('ERROR: The peer proxy is not available.')
            self.send_error(503)
            self.end_headers()
            return False
        #
        # check whether the incoming url can be converted into a outgoing url.
        # before it read the whole message from the cient.
        #
        if (not self.server.jc_mine.has_key(self.path) or
                not self.server.jc_mine[self.path].has_key('ou')):
            print('ERROR: no url mapping for %s' % self.path)
            self.send_error(404)
            self.end_headers()
            return False
        return True

    def post_read(self, contents):
        '''
        it called after the whole message from the client has been read.
        '''
        #
        # convert Path into the outgoing URL, and Host into the HTTP server.
        #
        a = inet_string(self.server.jc_mine[self.path]['ou'])
        self.headers = dict(self.headers)
        if self.headers.has_key('host'):
            if is_debug(2, self.server.west):
                print('DEBUG: convert Host into %s from %s' %
                      (self.headers['host'], a['url_host']))
            self.headers['host'] = a['url_host']
        if is_debug(2, self.server.west):
            print('DEBUG: convert Path into %s from %s' %
                  (self.path, a['url_path']))
        #
        msg_list = []
        msg_list.append(' '.join([self.command, a['url_path'],
                                  self.request_version]))
        msg_list.append('\r\n')
        msg_list.extend(['%s: %s\r\n' %
                         (k,v) for k,v in self.headers.iteritems()])
        msg_list.append('\r\n')
        msg_list.extend(contents)
        #
        msg = ''.join(msg_list)
        if is_debug(1, self.server.west):
            print('DEBUG: sending proxy message length=', len(msg))
            if is_debug(2, self.server.west):
                print('DEBUG: ---BEGIN: proxy server sending---')
                print(msg)
                print('DEBUG: ---END---')
        #
        '''
        http sessions must be identified.
        each session must be assigned uuid.
        chunked data have to be assiened an identical uuid.
        '''
        self.session_id = str(uuid.uuid4())
        #
        # double check again whether there is a socket for the peer.
        #
        if self.server.s_ws:
            response = self.server.s_ws.send(self, msg, self.session_id,
                                            proxy_protocol='http')
        else:
            print('ERROR: The peer proxy is not available.')
            self.send_error(503)
            self.end_headers()
            return
        #
        # waiting for a response from the server
        #
        if is_debug(1, self.server.west):
            print('DEBUG: waiting for response from http server in %d seconds' %
                  self.server_response_timer)
        self.waiting_for_server = Event()
        self.waiting_for_server.wait(self.server_response_timer)
        if not self.waiting_for_server.is_set():
            print('INFO: timeout for waiting a response from http server')

    '''
    "self.waiting_for_server.set()" must be called when this function finishes.

    @param response http header and payload, or None
    '''
    def reply(self, session_id, firstline, headers, content):
        if session_id != self.session_id:
            print('ERROR: unexpected session_id %s, should be %s',
                    session_id, self.session_id)
            self.waiting_for_server.set()
            return
        try:
            #
            # failed
            #
            if firstline[1] != '200':
                print('ERROR: http error code %s' % firstline[1])
                self.send_error(int(firstline[1]))
                self.end_headers()
                self.waiting_for_server.set()
                return
            #
            # success
            #
            if is_debug(1, self.server.west):
                print('DEBUG: sending back message length=%d' % len(content))
                if is_debug(2, self.server.west):
                    print('DEBUG: ---BEGIN: proxy server replying---')
                    print(''.join(['%s: %s\n' %
                                   (k, v) for k, v in headers.iteritems()]))
                    print(content)
                    print('DEBUG: ---END---')
            self.send_response(200)
            for k, v in headers.iteritems():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(content)
            self.wfile.write('\r\n')    # just make it sure
        except Exception:
            print(traceback.format_exc())
        self.waiting_for_server.set()

'''
FIAP Proxy Server
'''
class http_proxy_server(ThreadingMixIn, HTTPServer):

    #
    # pointer to the WS socket.
    # for a west client, it should be set in the initial.
    # for a west server, it should be set when a west client connects to the
    # server.
    #
    s_ws = None

    '''
    @param pss_name proxy server's address and port
    @param ps_config proxy server's config instance
    @param wst a WebSocket tunnel client's instance
    '''
    def __init__(self, west, pss_name):
        self.west = west
        self.pss_name = pss_name
        self.jc_mine = west.jc['proxy'][pss_name]
        #
        # existency check of ea and en must be done in west_config.
        #
        if self.jc_mine.has_key('ea'):
            if not west.jc['wstc'].has_key(self.jc_mine['ea']):
                print('FATAL: no wstc config for %s' % self.jc_mine['ea'])
                raise SystemError
            if not west.jc['wstc'][self.jc_mine['ea']].has_key('so'):
                # for a client configuration, a west client must have connected
                # to a west server.
                print('FATAL: west client has not been started on %s.' %
                      self.jc_mine['ea'])
                raise SystemError
            self.s_ws = west.jc['wstc'][self.jc_mine['ea']]['so']
        #
        HTTPServer.__init__(self, (self.jc_mine['addr'], self.jc_mine['port']),
                            ProxyHandler, bind_and_activate=True)

if __name__ == '__main__' :
    if len(sys.argv) != 2:
        print('Usage: this (config)')
        print('    e.g. this config.json')
        exit(1)
    try:
        config = west_config(sys.argv[1], debug_level=1)
    except Exception as e:
        print(e)
        exit(1)
    this = http_proxy_server(config, debug_level=1)
    this.go()


