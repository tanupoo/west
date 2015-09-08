#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import httplib
from inet_string import inet_string
import threading
from debug_tools import is_debug, debug_print

class http_proxy_http_client():

    def __init__(self, url, debug_level=0):
        a = inet_string(url)
        if not a['host']:
            print('ERROR: invalid url [%s]' % url)
            return
        server = a['host']
        if a['port']:
            server = '%s:%s' % (a['host'], a['port'])
        if debug_level:
            print('DEBUG: connecting to %s' % server)
        self.conn = httplib.HTTPConnection(server)
        self.server_addr = server
        self.path = a['url_path'] if a['url_path'] else '/'
        self.debug_level = debug_level

    def send_get(self, headers={}):
        try:
            self.conn.request("GET", self.path, '', headers)
            return self.get_response()
        except Exception as e:
            print(e)

    def send_post(self, message, headers={}):
        self.conn.request("POST", self.path, message, headers)
        return self.get_response()

    def get_response(self):
        try:
            ret = self.conn.getresponse()
            print('DEBUG: reponse from a server', ret.status, ret.reason)
            headers = ret.getheaders()
            data = ret.read()
            self.conn.close()
            return headers, data
        except Exception as e:
            print(e)

def http_proxy_http_client_func(wst_req, wst_res, conf, debug_level):
    if debug_level:
        print('DEBUG:', threading.currentThread().getName())
    c = http_proxy_http_client(conf['hr'][1], debug_level=debug_level)
    try:
        headers, response = c.send_post(conf['hc'], headers=conf['hh'])
    except Exception as e:
        print(e)
        # XXX send_resopnse('Connection refused')
        return
    if debug_level:
        print('DEBUG: response data length=', len(response))
        if debug_level > 1:
            print('DEBUG: ---BEGIN OF SENDING DATA---')
            print(response)
            print('DEBUG: ---END OF SENDING DATA---')
    #
    # since the response contains the whole message from the HTTP server,
    # if the response is 'transfer-encoding: chunked', it will be removed
    # and add content-length instead.
    #
    headers = dict(headers)
    e = headers.get('transfer-encoding')
    if e == 'chunked':
        headers.pop('transfer-encoding')
    headers['content-length'] = len(response)
    #
    # XXX check the response
    msg_list = []
    msg_list.extend(['%s: %s\r\n' % (k,v) for k,v in conf['wh'].items()])
    msg_list.append('\r\n')
    msg_list.extend(['%s: %s\r\n' % (k,v) for k,v in headers.items()])
    msg_list.append('\r\n')
    msg_list.append(response)
    msg = ''.join(msg_list)
    if debug_level:
        print('DEBUG: response message(len=%d)' % len(msg))
        if debug_level > 1:
            print('DEBUG: ---BEGIN OF RESPONSE---')
            print(msg)
            print('DEBUG: ---END OF RESPONSE---')
    wst_res.reply(wst_req, msg)

def http_proxy_http_client_thread(wst_req, wst_res, conf, debug_level=0):
    t = threading.Thread(target= http_proxy_http_client_func,
                            args= (wst_req, wst_res, conf, debug_level))
    t.daemon = False
    t.start()

if __name__ == '__main__' :
    if len(sys.argv) < 2:
        print('Usage: this (url) ["post" (message)]')
        print('    e.g. this http://127.0.0.1:9931/a')
        print('         this http://127.0.0.1:9931/a post hogehoge')
        exit(1)
    this = http_proxy_client(sys.argv[1], debug_level=1)
    if len(sys.argv) == 4:
        print(this.send_post(sys.arg[3]))
    else:
        print(this.send_get())

