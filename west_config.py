#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json
from inet_string import inet_string

class west_json_encoder(json.JSONEncoder):

    def default(self, o):
        #if o.hasattr(west) and o.west.hasattr(jc) and o.west.jc.has_key('so'):
        #    return 'socket'
        return dir(o)

class west_config(dict):

    config = None   # config in json
    west_name = ''
    allow_clients = {}

    '''
    west := {
      * 'nm': <default origin name>,
      * 'cp': <address and port number for control>,  # e.g. ":9702"
        'addr': <host name>,
        'port': <(int) port nuumber>,
        'so': <listening socket>
    }

    wsts := {
      * 'sp' : <west server URL>,                 # e.g. "ws://127.0.0.1:9801"
        'addr' : <west server host name>          # i.e. '127.0.0.1'
        'port' : <(int) west server port number>  # i.e. 9801
      * 'ca' : [ <access list ...> ],
        'so' : <west_server listening socket>,
        'end' : {                                 # client list for west_server
            'ws://client.fiap.org': {             # client's origin name, 'en'
                'so': <west_server thread instance>,
                'ea': <IP address and port of the client>,
                'rxc': <number of received data>,
                'rxs': <total size of received data>,
                'txc': <number of sent data>,
                'txs': <total size of sent data>
            }, { ... }
        }
    }

    wstc := {                                    # server list for west_client
      * 'ws://server.fiap.org': {                # server's address, 'ea'
      *     'ee': 'no',
      *     'nm': 'ws://client.fiap.org',        # origin name for this server
            'so': <west_client instance>,
            'rxc': <number of received data>,
            'rxs': <total size of received data>,
            'txc': <number of sent data>,
            'txs': <total size of sent data>
        }, { ... }
    }

    proxy := {
      * '<proxy URL address>' : {
      *     '<en or ea>' : 'west peer name',
            'addr' : <proxy host name>,
            'port' : <proxy port number>,
      *     '<proxy incoming URL>' : {
      *         'ou' : '<proxy outgoing URL>',
      *         'ca" : [ ]
            }, { ... }
        }, { ... }
    }

    '''

    def __init__(self, filename, debug_level=0):
        try:
            jc = json.loads(open(filename).read())
        except:
            raise
        self['debug_level'] = debug_level
        dict.__init__(self, jc)
        # check whether valid objects are defined.
        for i in jc:
            if i not in [ 'west', 'wsts', 'wstc', 'proxy' ]:
                raise ValueError('invalid object is defined. (%s)' % i)
        # keep this order to check the objects.
        self._check_west()
        self._check_wsts()
        self._check_wstc()
        self._check_proxy()

    def _check_west(self):
        '''
        check the west object
        '''
        if not self.has_key('west'):
            raise ValueError('the west object is required.')
        c = self['west']
        self.west_name = c.get('nm')
        if not self.west_name:
            raise ValueError('nm attribute in the west object is required.')
        if c.has_key('cp'):
            a = inet_string(c['cp'])
            c['addr'] = a['host']
            c['port'] = int(a['port'])

    def _check_wsts(self):
        '''
        check the wsts object
        '''
        if not self.has_key('wsts'):
            self['wsts'] = {}
        c = self['wsts']
        if c.has_key('sp'):
            a = inet_string(c['sp'])
            c['addr'] = a['host']
            c['port'] = int(a['port'])
        if c.has_key('ca'):
            print('WARNING: key "ca" is not supported yet.')

    def _check_wstc(self):
        '''
        check the wstc object
        '''
        if not self.has_key('wstc'):
            self['wstc'] = {}
        c = self['wstc']
        for i in c.iterkeys():
            #
            if c[i].has_key('ee'):
                if c[i]['ee'] not in [ 'yes', 'no' ]:
                    print('ERROR: at %s in wstc object' % i)
                    raise('value of "ee" must be either yes or no')
            #
            # set default if nm is not defined.
            #
            if not c[i].has_key('nm'):
                c[i]['nm'] = self.west_name

    def _check_proxy(self):
        '''
        check the proxy object
        '''
        if not self.has_key('proxy'):
            self['proxy'] = {}
        c = self['proxy']
        for i in c.iterkeys():
            a = inet_string(i)
            if not a['host']:
                print('ERROR: invalid proxy server name = %s' % pss_name)
                raise ValueError
            c[i]['addr'] = a['host']
            if not a['port']:
                a['port'] = 18889
            c[i]['port'] = int(a['port'])
            #
            if c[i].has_key('ea') and c[i].has_key('en'):
                print('ERROR: only "ea" or "en" can be specified.')
                raise ValueError
            if not c[i].has_key('ea') and not c[i].has_key('en'):
                print('ERROR: either "ea" or "en" is required at least.')
                raise ValueError
            #
            if c[i].has_key('ea'):
                j = c[i]['ea']
                if j not in self['wstc']:
                    self['wstc'][j] = { 'ee' : 'yes', 'nm' : self.west_name }
            elif c[i].has_key('en'):
                j = c[i]['en']
                if j not in self['wstc']:
                    self['wstc'][j] = { 'ee' : 'no', 'nm' : self.west_name }
            #
            # configuration for the url mapping.
            #
            for j in c[i].iterkeys():
                if j in [ 'ea', 'en', 'addr', 'port' ]:
                    continue
                if not j[0] == '/':
                    raise ValueError('invalid keyword= %s' % c[i][j])
                for k in c[i][j]:
                    p = c[i][j]
                    #
                    if not p.has_key('ou'):
                        raise ValueError(
                                'key "ou" is requred in %s%s.' % (i, j))
                    #
                    if p.has_key('ca'):
                        if not isinstance(p['ca'], list):
                            raise ValueError(
                                    'key "ca" must be a list in %s%s.' % (i, j))

    def print_state(self):
        print(self.get_state())

    def get_state(self):
        r = []
        for i in [ 'west', 'wsts', 'wstc', 'proxy' ]:
            r.append('--- %s object ---\n' % i)
            r.append(json.dumps(self[i], sort_keys=True, indent=4,
                             separators=(',', ':'), cls=west_json_encoder))
            r.append('\n')
        return ''.join(r)

'''
test code
'''
if __name__ == '__main__' :
    if len(sys.argv) != 2:
        print('Usage: this (config)')
        print('    e.g. this config.json')
        exit(1)
    #
    config = west_config(sys.argv[1], debug_level=3)
    config.print_state()

