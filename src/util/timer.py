#!/usr/bin/env python
#coding:utf-8

import time
from util.log import logger

def timer(content):
    def dercorator(fn):
        def wrapper(*args):
            pre = time.time()
            fn(*args)
            cost = (time.time() - pre) * 1000
            logger.info('%s, cost[%s]' % (content, cost))
        return wrapper
    return dercorator
                
