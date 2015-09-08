#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import argparse
import select
import threading
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from west_client import west_client
from west_server import west_server
from west_config import west_config
from west_control import west_control
from http_proxy_server import http_proxy_server
from debug_tools import is_debug, debug_print

class west():

    timeout = 0.5
    jc = None

    def __init__(self, config, debug_level=0):
        self.config_file = config
        if self.config_file:
            try:
                self.jc = west_config(self.config_file, debug_level=debug_level)
            except Exception as e:
                print('ERROR:', e)
                raise

    def go(self):
        try:
            self.start_wsts()
            self.start_wstc()
            self.start_proxy()
            self.start_cport()
        except Exception as e:
            print('ERROR:', e)
            if is_debug(1, self):
                raise
        #
        if is_debug(2, self):
            self.jc.print_state()
        #
        sock_list = []
        sock_list.extend(self.s_proxy)
        sock_list.extend(self.s_wstc)
        if self.s_wsts:
            sock_list.append(self.s_wsts)
        sock_list.append(self.s_cport)
        #
        try:
            while True:
                (r, [], []) = select.select(sock_list, [], [], self.timeout)
                for i in self.s_proxy:
                    if i in r:
                        print('INFO: received on a proxy port',
                              i.server_address)
                        i._handle_request_noblock()
                for i in self.s_wstc:
                    if i in r:
                        print('INFO: received on west client port', i)
                        i._handle_request_noblock()
                if self.s_wsts in r:
                    print('INFO: received on west server port',
                        self.s_wsts.server_address)
                    self.s_wsts._handle_request_noblock()
                if self.s_cport in r:
                    print('INFO: received on the control port',
                        self.s_cport.server_address)
                    self.s_cport._handle_request_noblock()
        except KeyboardInterrupt:
            print()
            print('INFO: terminated by keyboard interrupt.')
        except Exception as e:
            print('ERROR:', e)
            if is_debug(1, self):
                raise

    #
    # start wst server.
    #
    def start_wsts(self):
        self.s_wsts = None
        if self.jc['wsts'].has_key('sp'):
            self.s_wsts = west_server(self)
            print('INFO: west server has been started on %s' %
                  self.jc['wsts']['sp'])

    #
    # start wst clients and proxy servers.
    #
    def start_wstc(self):
        #
        # start wst clients by the wst_ends list
        #
        self.s_wstc = []
        obj = self.jc['wstc']
        for i in obj.iterkeys():
            if obj[i].has_key('ee') and obj[i]['ee'] == 'no':
                continue
            s = west_client(self, i)
            print('INFO: west client has connected to', i)
            self.s_wstc.append(s)

    #
    # start wst clients and proxy servers.
    #
    def start_proxy(self):
        #
        # start wst clients and proxy server by the proxy object
        #
        self.s_proxy = []
        obj = self.jc['proxy']
        for i in obj.iterkeys():
            s = http_proxy_server(self, i)
            print('INFO: proxy server has been started on %s', i)
            self.s_proxy.append(s)
            #
            if obj[i].has_key('en'):
                wsname = obj[i]['en']
            elif obj[i].has_key('ea'):
                wsname = obj[i]['ea']
            print('INFO: waiting for connection from %s', wsname)

    def update_proxy_server_callback(self, pss, end_name):
        if is_debug(2, self):
            print('DEBUG: updating proxy callback for west client %s' %
                  end_name)
        for i in self.s_proxy:
            if i.jc_mine.has_key('en') and i.jc_mine['en'] == end_name:
                if i.s_ws:
                    #
                    # simply update the callback because a west client might not
                    # terminate the last session normally.
                    #
                    print('WARNING: proxy %s has a callback' % i.pss_name)
                i.s_ws = pss
                if is_debug(2, self):
                    print('DEBUG: update callback of proxy %s' % i.pss_name)
        return True

    def remove_proxy_server_callback(self, pss, end_name):
        if is_debug(2, self):
            print('DEBUG: removing proxy callback for west client %s' %
                  end_name)
        for i in self.s_proxy:
            if i.jc_mine.has_key('en') and i.jc_mine['en'] == end_name:
                if not i.s_ws:
                    print('ERROR: proxy %s has not a callback' %
                          i.pss_name)
                    return False
                i.s_ws = None
                if is_debug(2, self):
                    print('DEBUG: remove callback of proxy %s' % i.pss_name)
        return True


    #
    # start the control port.
    #
    def start_cport(self):
        self.s_cport = west_control(self)
        print('INFO: control port has been started on %s %d' %
              (self.jc['west']['addr'], self.jc['west']['port']))

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-c', action='store', dest='config', default='',
        help="specify the configuration file.")
    p.add_argument('-O', action='store', dest='outfile', default='-',
        help="specify a output file, default is stdout.")
    p.add_argument('-v', action='store_true', dest='f_verbose', default=False,
        help="enable verbose mode.")
    p.add_argument('-d', action='append_const', dest='_f_debug',
                   default=[], const=1, help="increase debug mode.")
    p.add_argument('--input', action='store', dest='infile', default='-',
        help="specify an input file, default is stdin.")
    p.add_argument('--output', action='store', dest='outfile', default='-',
        help="specify an output file, default is stdout.")
    p.add_argument('--verbose', action='store_true', dest='f_verbose',
                   default=False, help="enable verbose mode.")
    p.add_argument('--debug', action='store', dest='_debug_level', default=0,
        help="specify a debug level.")
    p.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = p.parse_args()
    args.debug_level = len(args._f_debug) + int(args._debug_level)

    return args

import traceback
if __name__ == '__main__' :
    opt = parse_args()
    if opt.debug_level:
        print('DEBUG: debug level=%d' % opt.debug_level)
    try:
        this = west(config=opt.config, debug_level=opt.debug_level)
        this.go()
    except Exception as e:
        if opt.debug_level:
            print(traceback.print_exc())
        exit(1)
