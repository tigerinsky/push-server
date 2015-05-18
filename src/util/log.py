#!/usr/bin/env python
#coding:utf-8
import logging
import logging.handlers
import os
import sys

class Log(object):
    def __init__(self, name):
        self.name      = name
        self.log       = None
        self.fmt       = None
        self.formatter = None
        self.handler   = None

    def init(self):
        self.log     = logging.getLogger()
        #self.handler = logging.handlers.RotatingFileHandler(self.name, maxBytes=20*1024*1024,backupCount=10)
        #self.handler = logging.handlers.TimedRotatingFileHandler(self.name,'D',1,14)
        self.handler = logging.handlers.TimedRotatingFileHandler(self.name,'midnight',1,14)
        self.handler.suffix = "%Y%m%d"
        self.fmt     = '%(asctime)s %(levelname)s - %(message)s '
        self.formatter = logging.Formatter(self.fmt)
        self.handler.setFormatter(self.formatter)
        self.log.addHandler(self.handler)
        self.handler = logging.StreamHandler(sys.stdout)
        self.handler.setFormatter(self.formatter)
        #self.log.addHandler(self.handler)
        self.log.setLevel(logging.NOTSET)

    def debug(self, content):
        self.log.debug(content)

    def info(self, content):
        self.log.info(content)

    def warning(self, content):
        self.log.warning(content)

    def error(self, content):
        self.log.error(content)

    def critical(self, content):
        self.log.critical(content)

LOG_NAME = os.path.join("log/", "push-server.log")
logger = Log(LOG_NAME)
logger.init()
