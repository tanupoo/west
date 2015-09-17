#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import re

valid_keys = ['TransactionOrigin', 'TransactionID', 'X-Proxy-Protocol' ]

re_http_response = re.compile('HTTP/\d+\.\d+')

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
        raise ValueError('ERROR: no message is passed.')
    # parse the west header
    wst_header, sep, http_message = message.partition('\r\n\r\n')
    if sep != '\r\n\r\n':
        raise ValueError('ERROR: there is no double CR+LF for the end of wst header.')
    for m in wst_header.split('\r\n'):
        key, val = m.split(':', 1)
        key = key.strip()
        val = val.strip()
        if not key in valid_keys:
            print('WARNING: unknown key %s has been found.' % key)
        wst_msg['wh'].update({ key : val })
    # parse the http header
    http_headers, sep, wst_msg['hc'] = http_message.partition('\r\n\r\n')
    if sep != '\r\n\r\n':
        raise ValueError('ERROR: there is no double CR+LF for the end of http header.')
    http_1stline, sep, http_headers = http_headers.partition('\r\n')
    #
    # don't check whether sep is equal to '\r\n' because there is a case
    # when the peer doesn't send other http headers nor any content.
    #
    #if sep != '\r\n':
    #    raise ValueError('ERROR: there is no CR+LF for the end of http first line.')
    wst_msg['hr'] = http_1stline.split(' ', 2)
    ret = re_http_response.match(wst_msg['hr'][0])
    if ret:
        # http response
        errcode = int(wst_msg['hr'][1])
    else:
        ret = re_http_response.match(wst_msg['hr'][2])
        if ret:
            # http request
            pass
        else:
            raise ValueError('ERROR: invalid HTTP first line [%s]' % wst_msg['hr'])
    # XXX need more check about the commands
    for h in http_headers.split('\r\n'):
        if not h:
            continue
        key, val = h.split(':', 1)
        key = key.strip().lower()
        val = val.strip()
        wst_msg['hh'].update({ key : val })
    return wst_msg

