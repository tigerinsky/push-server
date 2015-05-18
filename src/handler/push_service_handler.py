#!/usr/bin/env python
#coding:utf-8

import sys
sys.path.append('../gen-py')
import time
import httplib
import urllib
import json
import random

from third import xinge
import gevent
import gevent.monkey

from push import PushService
from push.ttypes import *
from util.log import logger
from util.timer import timer
from util import http
from config.const import SUCCESS, PARAM_NOTIFY_ERROR, PARAM_LIST_ERROR, \
                         MSG_ERROR, BROADCAST_ERROR, RET_UNKNOWN_ERROR

NOTIFY_EXPIRE_TIME = 86400 #TODO 移到配置文件中
ANDROID_ACCESS_ID = 2100084785
ANDROID_ACCESS_TOKEN = '0846d3db888ec8346a5c0b70a702e407'
IOS_ACCESS_ID = 2200098803
IOS_ACCESS_TOKEN = '5719cb32acd728b1ae3bdafa6f8db7a1'
SCHEMA_PREFIX = 'myb://'

gevent.monkey.patch_all(ssl=False)

SCHEMA = {
    LandingType.INDEX: '%s%s' % (SCHEMA_PREFIX, 'index'),
    LandingType.WAP: '%s%s' % (SCHEMA_PREFIX, 'wap'),
    LandingType.COMMUNITY_DETAIL: '%s%s' % (SCHEMA_PREFIX, 'tweet'),
    LandingType.FRIEND: '%s%s' % (SCHEMA_PREFIX, 'friend'),
    LandingType.PRIVATE_MSG: '%s%s' % (SCHEMA_PREFIX, 'pmsg'),
    LandingType.SYSTEM_MSG: '%s%s' % (SCHEMA_PREFIX, 'smsg')
    LandingType.USER: '%s%s' % (SCHEMA_PREFIX, 'user')
}

class PushServiceHandler:
    def __init__(self):
        self.android_push_app = xinge.XingeApp(ANDROID_ACCESS_ID, ANDROID_ACCESS_TOKEN)
        self.ios_push_app = xinge.XingeApp(IOS_ACCESS_ID, IOS_ACCESS_TOKEN)

    def _build_schema(self, notify):
        ltype = notify.ltype
        url = SCHEMA.get(ltype, '')
        param = {}

        if ltype == NotifyType.WAP:
            param['url'] = notify.url
        elif ltype == NotifyType.COMMUNITY_DETAIL:
            param['tid'] = notify.tid
        elif ltype == NotifyType.PRIVATE_MSG or ltype == NotifyType.USER:
            param['uid'] = notify.uid

        if url and param:
            params = urllib.urlencode(param)
            url = '%s?%s' % (url, params)

        return url

    def _get_msg_custom(self, notify):
        custom = {}
        custom['t'] = notify.mtype
        param = {}
        schema = ''
        if mtype == MessageType.NOTIFY:#类型为通知，需要生成schema
            schema = self._build_schema(notify)
        elif mtype == MessageType.EMAILRED: #类型为私信小红点，需额外uid参数，告诉客户端是哪个人的小红点
            param['uid'] = notify.uid
            
        param['j'] = schema
        custom['p'] = param
        return custom

    def _build_android_msg(self, notify):
        '''定义通知消息'''
        msg = xinge.Message()
        msg.type = xinge.Message.TYPE_MESSAGE
        msg.title = notify.title
        msg.content = notify.content
        msg.expireTime = NOTIFY_EXPIRE_TIME#TODO 小红点需要expire吗
        msg.custom = self._get_msg_custom(notify)
        return msg

    def __build_ios_msg(self, notify):
        msg = xinge.MessageIOS()
        msg.alert = notify.content
        if notify.mtype == MessageType.NOTIFY:
            msg.sound = 'default'
            msg.badage = 1
        msg.expireTime = NOTIFY_EXPIRE_TIME
        msg.custom = self._get_msg_custom(notify)
        return msg

    @timer('push end')
    def _push_single_device(self, device_id, msg, device_type, env=1):#xinge.XingeApp.ENV_DEV):#ios上线要修改
        result = None
        if device_type == DeviceType.ANDROID:
            logger.info('push start:device_id[%s] device_type[%s] msg_type[%s] title[%s] content[%s] expire[%s] custom[%s]' % (device_id, device_type, msg.type, msg.title, msg.content, msg.expireTime, msg.custom))
            result = self.android_push_app.PushSingleDevice(device_id, msg, env)
        elif device_type == DeviceType.IOS:
            logger.info('push start:device_id[%s] device_type[%s] sound[%s] title[%s] content[%s] expire[%s] custom[%s]' % (device_id, device_type, msg.sound, '', msg.alert, msg.expireTime, msg.custom))
            result = self.ios_push_app.PushSingleDevice(device_id, msg, env)
        logger.info('result[%s] device_id[%s]' % (result, device_id)) 
    
    def ping(self): 
        return 'hello, world'

    def _build_msg(notify, device_type):
        msg = None
        if device_type == DeviceType.IOS:
            msg = _build_ios_msg(notify)
        elif device_type == DeviceType.ANDROID:
            msg = _build_android_msg(notify)
        else:
            logger.warning('msg[device type error] device_type[%s] notify[%s]' % (device_type, notify))

        return msg

    @timer('batch notify over')
    def batch_notify(self, request):
        logger.info('batch notify request begin, request[%s]' % request)
        notify = request.notify;
        if not isinstance(notify, Notify):
            logger.warning('param notify is not instance of notify')
            return PARAM_NOTIFY_ERROR

        device_id_list = request.device_id_list;
        if not isinstance(device_id_list, list):
            logger.warning('param device_id_list is invalid')
            return PARAM_LIST_ERROR
        if len(device_id_list) <= 0:
            return SUCCESS

        device_type = request.device_type
        msg = _build_msg(notify, device_type)

        if not msg:
            logger.warning('msg[msg generate error]')
            return MSG_ERROR

        send_time = None
        if hasattr(request, 'send_time'):
            t = request.send_time
            send_time = '1970-01-01 00:00:00'
            try:
                x = time.localtime(t)
                send_time = time.strftime("%Y-%m-%d %H:%M:%S", x)
            except Exception, e:
                logger.warning('time trans exception,e[%s]' % e)
        if send_time:
            msg.sendTime = send_time

        threads = [gevent.spawn(self._push_single_device, device_id, msg, request.device_type) for device_id in device_id_list]
        gevent.joinall(threads)

        return SUCCESS

    @timer('single push called cost')
    def single_notify(self, request):
        device_id = request.device_id
        notify = request.notify
        device_type = request.device_type
        if not isinstance(notify, Notify):
            logger.warning('msg[param error] param[%s]' % request)
            return PARAM_NOTIFY_ERROR
        if not msg:
            logger.warning('msg[msg generate error]')
            return MSG_ERROR

        msg = _build_msg(notify, device_type)
        gevent.spawn(self.__push_single_device, device_id, msg, device_type)
        logger.info('single push called over')
        return SUCCESS

    @timer('broadcast end')
    def broadcast(self, request):
        logger.info('broadcast begin request[%s]' % request)
        notify = request.notify
        send_time = None
        if hasattr(request, 'send_time'):
            t = request.send_time
            send_time = '1970-01-01 00:00:00'
            try:
                x = time.localtime(t)
                send_time = time.strftime("%Y-%m-%d %H:%M:%S", x)
            except Exception, e:
                logger.warning('time trans exception,e[%s]' % e)
        if not isinstance(notify, Notify):
            logger.warning('param notify is invalid')
            return PARAM_NOTIFY_ERROR

        device_type = request.device_type
        msg = self._build_msg(notify, device_type)
        if not msg:
            logger.warning('msg[msg generate error]')
            return MSG_ERROR

        if send_time:
            msg.sendTime = send_time

        ret = None
        if device_type == DeviceType.ANDROID:
            ret = self.android_push_app.PushAllDevices(0, msg)
        if device_type == DeviceType.IOS:
            ret = self.ios_push_app.PushAllDevices(0, msg, 1)
        logger.info('ret[%s]' % ret)
        if ret:
            if ret[0] == 0:
                return SUCCESS
            else:
                return BROADCAST_ERROR

        return RET_UNKNOWN_ERROR
