#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re

'''
it return a hash list
    {
        'url_scheme' : '<url_scheme>',
          'url_host' : '<url_host>',
          'url_path' : '<ulr_path>',
              'host' : '<ip address or host name>',
              'port' : '<port number or service name>'
    }
if there is no matched part, it set '' (null).
'''

re_url = re.compile('^(\w+)://([^/]+)(|/.*)$')
re_brackets = re.compile('^\[([^]]+)\](|:([a-zA-Z0-9]+))$')
re_anyaddr = re.compile('^:(\d+)')
re_ipv6_addr = re.compile('^([a-fA-F0-9:]+)$')
re_non_brackets = re.compile('^([a-zA-Z0-9\-\.]+)(|:([a-zA-Z0-9]+))$')

def inet_string(s, lookup=False):
    ret = {
        'url_scheme' : '',
          'url_host' : '',
          'url_path' : '',
              'host' : '',
              'port' : ''
    }
    if len(s) == 0:
        return ret
    if s[0] == '/':
        ret['url_path'] = s
        return ret
    # cut the host part
    r = re_url.match(s)
    if r:
        ret['url_scheme'] = r.group(1)
        ret['url_path'] = r.group(3)
        ret['url_host'] = r.group(2)
        s = r.group(2)
    # cut the port number
    r = re_brackets.match(s)
    if r:
        ret['host'] = r.group(1)
        ret['port'] = r.group(3) if r.group(3) else ''
    else:
        r = re_anyaddr.match(s)
        if r:
            ret['host'] = ''
            ret['port'] = r.group(1)
        else:
            r = re_ipv6_addr.match(s)
            if r:
                ret['host'] = r.group(1)
            else:
                r = re_non_brackets.match(s)
                if r:
                    ret['host'] = r.group(1)
                    ret['port'] = r.group(3) if r.group(3) else ''
                else:
                    ret['host'] = s
    '''
    re_ipv6_a_p = re.compile('^\[([0-9a-fA-F:]+)\](|:\d+)$')
    re_ipv6_a = re.compile('^([0-9a-fA-F:]+)$')
    re_ipv4_a_p = re.compile('^([0-9\.]+)(|:\d+)$')
    r = re_ipv6_a_p.match(s)
    if r:
        ret['addr'] = r.group(1)
        ret['port'] = r.group(2)[1:]
    else:
        r = re_ipv6_a.match(s)
        if r:
            ret['addr'] = r.group(1)
        else:
            r = re_ipv4_a_p.match(s)
            if r:
                ret['addr'] = r.group(1)
                ret['port'] = r.group(2)[1:]
    '''
    return ret

def pprint(s):
    print 'url_scheme =', s['url_scheme']
    print '  url_host =', s['url_host']
    print '  url_path =', s['url_path']
    print '      host =', s['host']
    print '      port =', s['port']

if __name__ == '__main__' :
    if len(sys.argv) != 2:
        print 'Usage: this (test|<inet_addr_string>)'
        exit(1)
    if sys.argv[1] == 'test':
        v = [
            'www.example.org',
            '192.168.0.1',
            '3ffe:5001::1',
            '[3ffe:5001::1]',
            ':9999',
            '::1',
            'www.example.org:9999',
            '192.168.0.1:9999',
            '[3ffe:5001::1]:9999',
            'http://www.example.org',
            'http://192.168.0.1',
            'http://3ffe:5001::1',
            'http://www.example.org:9999',
            'http://192.168.0.1:9999',
            'http://192.168.0.1:9999/',
            'http://[3ffe:5001::1]:9999',
            'http://www.example.org:9999/hoge',
            'http://192.168.0.1:9999/hoge',
            'http://[3ffe:5001::1]:9999/hoge',
            ]
        for i in v:
            print '--- ', i
            ret = inet_string(i)
            pprint(ret)
    else:
        ret = inet_string(sys.argv[1])
        pprint(ret)
