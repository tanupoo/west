#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from websocket import create_connection
from http_proxy_client import http_proxy_http_client_thread
from west_parser import west_parser
from debug_tools import is_debug, debug_print

WEST_HEADER = ['User-Agent: west.py 0.1']

'''
FIAP WebSocket Client
'''
class west_client():

    q_request = {}

    def __init__(self, west, wsts_addr):
        self.west = west
        self.wsts_addr = wsts_addr
        self.jc_mine = west.jc['wstc'][wsts_addr]
        try:
            #
            # XXX
            #    sslopt=
            #
            self.so = create_connection(self.wsts_addr, timeout=5,
                                        origin=self.jc_mine['nm'],
                                        header=WEST_HEADER)
            self.jc_mine['so'] = self
        except Exception:
            raise

    def fileno(self):
        return self.so.fileno()

    def send(self, proxy, payload, session_id, proxy_protocol=''):
        msg_list = []
        msg_list.append('TransactionOrigin: %s\r\n' % self.jc_mine['nm'])
        msg_list.append('TransactionID: %s\r\n' % session_id)
        if proxy_protocol:
            msg_list.append('X-Proxy-Protocol: %s\r\n' % proxy_protocol)
        msg_list.append('\r\n')
        msg_list.append(payload)
        msg = ''.join(msg_list)
        self.so.send(msg)
        if is_debug(1, self.west):
            print('DEBUG: sent wst message length=%d' % len(msg))
            if is_debug(2, self.west):
                print('DEBUG: ---BEGIN OF FORWARDING WST DATA---')
                print(msg)
                print('DEBUG: ---END OF FORWARDING WST DATA---')
        self.q_request[session_id] = proxy

    def _handle_request_noblock(self):
        try:
            msg =  self.so.recv()
        except Exception as e:
            print('ERROR:', e)
            raise
        if is_debug(1, self.west):
            print('DEBUG: received wst message length=%d' % len(msg))
            if is_debug(2, self.west):
                print('DEBUG: ---BEGIN OF FORWARDED WSTS DATA---')
                print(msg)
                print('DEBUG: ---END OF FORWARDED WSTS DATA---')
        ret = west_parser(msg)
        if not ret:
            raise ValueError
        #
        t_origin = ret['wh'].get('TransactionOrigin')
        if not t_origin:
            print('ERROR: TransactionOrigin does not exist.')
            raise ValueError
        t_id = ret['wh'].get('TransactionID')
        if not t_id:
            print('ERROR: TransactionID does not exist.')
            return ValueError
        #
        proxy = self.q_request.get(t_id)
        if proxy:
            #
            # response from the server.
            #
            proxy.put_response(t_id, ret['hh'], ret['hc'])
            self.q_request.pop(t_id)
            return
        #
        # new request from the client.
        #
        if is_debug(1, self.west):
            print('DEBUG: t_origin, t_id = %s, %s' % (t_origin, t_id))
            if is_debug(2, self.west):
                print('DEBUG: ---BEGIN OF SENDING TO PROXY CLIENT---')
                print('DEBUG: wst headers=', ret['wh'])
                print('DEBUG: http request=', ret['hr'])
                print('DEBUG: http headers=', ret['hh'])
                print('DEBUG: http content=')
                print(ret['hc'])
                print('DEBUG: ---END OF SENDING TO PROXY CLIENT---')
        #
        http_proxy_http_client_thread(None, self, ret,
                                    debug_level=self.west.jc['debug_level'])

    def reply(self, client, msg):
        self.so.send(msg)
