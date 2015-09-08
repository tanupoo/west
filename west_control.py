#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from debug_tools import is_debug, debug_print

class west_control_handle(BaseHTTPRequestHandler):

    def do_GET(self):
        #self.common_proc('GET')
        r = []
        r.append(self.server.west.jc.get_state())
        r.append(self.server.west.get_state())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(''.join(r))

class west_control(ThreadingMixIn, HTTPServer):

    def __init__(self, west):
        self.west = west
        jc_mine = west.jc['west']
        HTTPServer.__init__(self, (jc_mine['addr'], jc_mine['port']),
                            west_control_handle)
