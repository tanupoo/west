#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import threading

def debug_print(self, *args):
    class_name = repr(self.__class__).split()[1]
    thread_name = threading.currentThread().getName()
    print('DEBUG:', class_name, thread_name, args)
