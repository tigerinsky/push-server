#!/usr/bin/env python
#coding:utf-8

import urllib
import urllib2

from util.log import logger

def request(url, params, method='GET', timeout=1):
    result = None
    response = None
    if method == 'GET':
        url = '%s?%s' % (url, urllib.urlencode(params))
        logger.info('request url: %s' % url)
        try:
            response = urllib2.urlopen(url, timeout=timeout)
            result = response.read()
        except urllib2.URLError as e:
            code = e.code if hasattr(e, 'code') else -1
            reason = e.reason if hasattr(e, 'reason') else None
            logger.warning('url error, code[%s] reason[%s]' % (code, reason))
        except urllib2.HTTPError as e:
            code = e.code if hasattr(e, 'code') else -1
            logger.warning('http error, code[%s]' % (code))
        except Exception, e:
            logger.warning("url get exception, url: %s, e: %s" % (url, e))
        finally:
            if response:
                response.close()
    if method == 'POST':
        try:
            req = urllib2.Request(url, urllib.urlencode(params))
            response = urllib2.urlopen(req)
            result = response.read()
        except urllib2.URLError as e:
            code = e.code if hasattr(e, 'code') else -1
            reason = e.reason if hasattr(e, 'reason') else None
            logger.warning('url error, code[%s] reason[%s]' % (code, reason))
        except urllib2.HTTPError as e:
            code = e.code if hasattr(e, 'code') else -1
            logger.warning('http error, code[%s]' % (code))
        except Exception, e:
            logger.warning("url get exception, url: %s, e: %s" % (url, e))
        finally:
            if response:
                response.close()

    return result
