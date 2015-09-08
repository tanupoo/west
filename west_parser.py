#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

valid_keys = ['TransactionOrigin', 'TransactionID', 'X-Proxy-Protocol' ]

'''
@return { 'wh' : {}, 'hr' : [], 'hh' : {}, 'hc' : '' }
    wh: wst_headers
    hr: http_request
    hh: http_headers
    hc: http_content
'''
def west_parser(message):

    wst_msg = {
            'wh' : {},
            'hr' : [],
            'hh' : {},
            'hc' : ''
            }

    if not message:
        return None
    # parse the ws tunnel header
    wst_header, sep, http_message = message.partition('\r\n\r\n')
    if sep != '\r\n\r\n':
        print('ERROR: there is no double CR+LF for the end of wst header.')
        return None
    for m in wst_header.split('\r\n'):
        key, val = m.split(':', 1)
        key = key.strip()
        val = val.strip()
        if not key in valid_keys:
            print('WARNING: unknown key %s has been found.' % key)
        wst_msg['wh'].update({ key : val })
    # parse the http header
    http_header, sep, wst_msg['hc'] = http_message.partition('\r\n\r\n')
    if sep != '\r\n\r\n':
        print('ERROR: there is no double CR+LF for the end of http header.')
        return None
    http_request, sep, rest = http_header.partition('\r\n')
    wst_msg['hr'] = http_request.split(' ', 3)
    if len(wst_msg['hr']) < 2:
        print('ERROR: less parameters in the request line len=.',
              len(wst_msg['hr']))
    if sep != '\r\n':
        print('ERROR: there is no CR+LF for the end of http request line.')
        return None
    # XXX need more check about the commands
    for m in rest.split('\r\n'):
        key, val = m.split(':', 1)
        key = key.strip()
        val = val.strip()
        wst_msg['hh'].update({ key : val })
    return wst_msg

