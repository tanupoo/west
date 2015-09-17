#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import httplib
from inet_string import inet_string
import threading
from debug_tools import is_debug, debug_print

class http_proxy_http_client():
    #
    # XXX should it be replaced httplib ?
    #

    version_string = { 10:'HTTP/1.0', 11:'HTTP/1.1' }

    #
    # this class usually take a host name from url.
    # if host_in_header is specified, this class takes it.
    # this class doesn't check whether the host part in url is equal
    # to host_in_header.
    #
    def __init__(self, url, host_in_header=None, debug_level=0):
        self.debug_level = debug_level
        a = inet_string(url)
        if host_in_header:
            self.host = host_in_header
        elif a['url_host']:
            self.host = a['url_host']
        else:
            print('ERROR: Host field or URL host part are not defined.')
            return
        if self.debug_level:
            print('DEBUG: connecting to %s' % self.host)
        self.conn = httplib.HTTPConnection(self.host)
        self.path = a['url_path'] if a['url_path'] else '/'

    def send_get(self, headers={}):
        self.conn.request("GET", self.path, '', headers)
        return self.get_response()

    def send_post(self, message, headers={}):
        if self.debug_level > 1:
            print('DEBUG: ---BEGIN: proxy client sending---')
            print('POST', self.path)
            print(''.join([ '%s: %s\n' %
                           (k, v) for k, v in headers.iteritems() ]))
            print(message)
            print('DEBUG: ------')
        self.conn.request("POST", self.path, message, headers)
        return self.get_response()

    def get_response(self):
        ret = self.conn.getresponse()
        if self.debug_level:
            print('DEBUG: response from http server', ret.status, ret.reason)
        if not self.version_string.has_key(ret.version):
            raise ValueError('invalid version %d' % ret.version)
        firstline = ' '.join([self.version_string[ret.version],
                              str(ret.status), ret.reason])
        headers = ret.getheaders()
        data = ret.read()
        self.conn.close()
        return firstline, headers, data

def http_proxy_http_client_func(wst_req, wst_res, reqmsg, debug_level):
    if debug_level:
        print('DEBUG:', threading.currentThread().getName())
    if reqmsg['hh'].has_key('host'):
        host = reqmsg['hh']['host']
    else:
        raise ValueError('Host field does not exist.')
    c = http_proxy_http_client(reqmsg['hr'][1], host_in_header=host,
                               debug_level=debug_level)
    try:
        firstline, headers, response = c.send_post(reqmsg['hc'],
                                                headers=reqmsg['hh'])
    except Exception as e:
        #
        # errors like connection refused are assumed here.
        #
        print('ERROR:', e)
        msg_list = []
        msg_list.append('%s %d\r\n' % (reqmsg['hr'][2], 504))
        msg_list.extend(['%s: %s\r\n' %
                         (k, v) for k, v in reqmsg['hh'].iteritems()])
        msg_list.append('\r\n')
        msg_list.append(str(e))
        msg = ''.join(msg_list)
        wst_res.reply(wst_req, reqmsg, msg)
        return
    if debug_level:
        print('DEBUG: received data length=', len(response))
        if debug_level > 1:
            print('DEBUG: ---BEGIN: proxy client received---')
            print(response)
            print('DEBUG: ---END---')
    #
    # since the response contains the whole message from the HTTP server
    # even if it was chunked, so if the header of the response includes
    # 'transfer-encoding: chunked', it will be removed and adds
    # content-length instead.
    #
    headers = dict(headers)
    e = headers.get('transfer-encoding')
    if e == 'chunked':
        headers.pop('transfer-encoding')
    headers['content-length'] = len(response)
    #
    # XXX check the response
    #
    msg_list = []
    msg_list.append(firstline)
    msg_list.append('\r\n')
    msg_list.extend(['%s: %s\r\n' %
                     (k,v) for k,v in headers.iteritems()])
    msg_list.append('\r\n')
    msg_list.append(response)
    msg = ''.join(msg_list)
    #
    wst_res.reply(wst_req, reqmsg, msg)

def http_proxy_http_client_thread(wst_req, wst_res, reqmsg, debug_level=0):
    t = threading.Thread(target= http_proxy_http_client_func,
                            args= (wst_req, wst_res, reqmsg, debug_level))
    t.daemon = False
    t.start()

if __name__ == '__main__' :
    if len(sys.argv) < 2:
        print('Usage: this (url) ["post" (message)]')
        print('    e.g. this http://127.0.0.1:9931/a')
        print('         this http://127.0.0.1:9931/a post hogehoge')
        exit(1)
    this = http_proxy_client(sys.argv[1], debug_level=1)
    try:
        if len(sys.argv) == 4:
            print(this.send_post(sys.arg[3]))
        else:
            print(this.send_get())
    except Exception as e:
        print('ERROR:', e)

