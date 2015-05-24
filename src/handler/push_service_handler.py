#!/usr/bin/env python
#coding:utf-8

import sys
sys.path.append('./gen-py')
import time
import httplib
import urllib
import json
import random
import itertools

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

from model.user_push import UserPush
from model.user_detail import UserDetail

NOTIFY_EXPIRE_TIME = 86400 #TODO 移到配置文件中
ANDROID_ACCESS_ID = 2100106617
ANDROID_ACCESS_TOKEN = 'a797bf2b660b362736ea220a8e9f4b4e'#secret key
IOS_ACCESS_ID = 2200098803
IOS_ACCESS_TOKEN = '5719cb32acd728b1ae3bdafa6f8db7a1'
SCHEMA_PREFIX = 'meiyuan://'

gevent.monkey.patch_all(ssl=False)

SCHEMA = {
    LandingType.INDEX: '%s%s' % (SCHEMA_PREFIX, 'index'),
    LandingType.WAP: '%s%s' % (SCHEMA_PREFIX, 'wap'),
    LandingType.COMMUNITY_DETAIL: '%s%s' % (SCHEMA_PREFIX, 'tweet'),
    LandingType.FRIEND: '%s%s' % (SCHEMA_PREFIX, 'friend'),
    LandingType.PRIVATE_MSG: '%s%s' % (SCHEMA_PREFIX, 'pmsg'),
    LandingType.SYSTEM_MSG: '%s%s' % (SCHEMA_PREFIX, 'smsg'),
    LandingType.USER: '%s%s' % (SCHEMA_PREFIX, 'user'),
}

class PushServiceHandler:
    def __init__(self):
        self.android_push_app = xinge.XingeApp(ANDROID_ACCESS_ID, ANDROID_ACCESS_TOKEN)
        self.ios_push_app = xinge.XingeApp(IOS_ACCESS_ID, IOS_ACCESS_TOKEN)

    def _build_schema(self, notify):
        ltype = notify.ltype
        url = SCHEMA.get(ltype, '')
        param = {}

        if ltype == LandingType.WAP:
            param['url'] = notify.url
        elif ltype == LandingType.COMMUNITY_DETAIL:
            param['tid'] = notify.tid
        elif ltype == LandingType.PRIVATE_MSG or ltype == LandingType.USER:
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
        if notify.mtype == MessageType.NOTIFY:#类型为通知，需要生成schema
            schema = self._build_schema(notify)
        elif notify.mtype == MessageType.EMAILRED: #类型为私信小红点，需额外uid参数，告诉客户端是哪个人的小红点
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

    def _build_ios_msg(self, notify):
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

    def _build_msg(self, notify, device_type):
        msg = None
        if device_type == DeviceType.IOS:
            msg = self._build_ios_msg(notify)
        elif device_type == DeviceType.ANDROID:
            msg = self._build_android_msg(notify)
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
        msg = self._build_msg(notify, device_type)

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
        msg = self._build_msg(notify, device_type)
        if not msg:
            logger.warning('msg[msg generate error]')
            return MSG_ERROR

        gevent.spawn(self._push_single_device, device_id, msg, device_type)
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

    @timer('op tag end')
    def optag(self, request):
        logger.info('msg[optag begin] request[%s]' % request)
        if request.uid == 0 or not isinstance(request.uid, int):
            logger.warning('msg[invalid uid] uid[%s]' % request.uid)
            return PARAM_UID_ERROR

        token_group = {}
        if request.xg_device_token == '':
            r = UserPush.get_device_info(request.uid)
            for k, g in itertools.groupby(r, lambda x:x.device_type):
                token_group[k] = [i.xg_device_token for i in g]
        else:
            r = UserPush.get_device_type(request.xg_device_token)
            if not r:
                logger.warning('msg[no this token in table] token[%s]' % request.xg_device_token)
                return SUCCESS
            token_group.setdefault(r, []).append(request.xg_device_token)

        tag_list = request.tag_list
        tag_list.append('all_city')
        tag_list.append('all_school')

        for dtype in token_group:
            tag_token_list = []
            xg_device_token = token_group[dtype]
            for token in xg_device_token:
                if dtype == DeviceType.ANDROID:
                    l = [xinge.TagTokenPair(x, token) for x in tag_list+['android']] 
                if dtype == DeviceType.IOS:
                    l = [xinge.TagTokenPair(x, token) for x in tag_list+['ios']] 
                tag_token_list += l

            size = len(tag_token_list)
            num = 19 
            slice_tag_list = [tag_token_list[i:i+num] for i in range(0, size, num)]

            for l in slice_tag_list:
                result = (0, '')
                if dtype == DeviceType.ANDROID:
                    if request.op == 1:
                        result = self.android_push_app.BatchSetTag(l)
                    elif request.op == 2:
                        result = self.android_push_app.BatchDelTag(l)
                if dtype == DeviceType.IOS:
                    if request.op == 1:
                        result = self.ios_push_app.BatchSetTag(l)
                    elif request.op == 2:
                        result = self.ios_push_app.BatchDelTag(l)

                print result
                if result[0] != 0:
                    logger.warning('msg[set tag error] tags[%s] uid[%s] tagpair[%s] op[%s] ret[%s]' % (tag_list, request.uid, l, request.op, result))
                    print 'msg[set tag error] tags[%s] uid[%s] tagpair[%s] op[%s] ret[%s]' % (tag_list, request.uid, l, request.op, result)


        return SUCCESS

    def _tag_push(self, tag_list, msg, device_type, push_task_id):
        retry = 2
        ret = None
        for i in range(retry):
            if device_type == DeviceType.IOS:
                ret = self.ios_push_app.PushTags(0, tag_list, 'AND', msg, 1)
            if device_type == DeviceType.ANDROID:
                ret = self.android_push_app.PushTags(0, tag_list, 'AND', msg)
            logger.info('msg[condition push result] retry[%s] device_type[%s] tags[%s] msg[%s] ret[%s] push_task_id[%s]' % (i, device_type, tag_list, msg, ret, push_task_id))
            if ret[0] == 0:
                return ret[2]

        return -1


    def condition_push(self, request):
        logger.info('msg[condition push begin] request[%s]' % request)

        notify = request.notify
        push_task_id = request.push_task_id

        ios_msg = self._build_msg(notify, DeviceType.IOS)
        android_msg = self._build_msg(notify, DeviceType.ANDROID)

        city = request.city.split(',')
        school = request.school.split(',')
        ukind_verify = request.ukind_verify.split(',')

        task_list = []
        push_id_list = []
        i = 1
        for tag_list in itertools.product(city, school, ukind_verify):
            if request.device_type == 0:
                task_list.append(gevent.spawn(self._tag_push, tag_list, ios_msg, DeviceType.IOS, push_task_id))
                task_list.append(gevent.spawn(self._tag_push, tag_list, android_msg, DeviceType.IOS, push_task_id))
                i += 2
            if request.device_type == 1:
                task_list.append(gevent.spawn(self._tag_push, tag_list, android_msg, DeviceType.IOS, push_task_id))
                i += 1
            if request.device_type == 2:
                task_list.append(gevent.spawn(self._tag_push, tag_list, ios_msg, DeviceType.IOS, push_task_id))
                i += 1

            if i % 1000 == 0:#控制并发
                gevent.joinall(task_list, timeout=5)
                for task in task_list:
                    push_id_list.append(task.value)
                task_list = []

        gevent.joinall(task_list, timeout=5)
        for task in task_list:
            push_id_list.append(task.value)
        logger.info('push_task_id[%s] push_id_list%s' % (push_task_id, push_id_list))
