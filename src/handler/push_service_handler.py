#!/usr/bin/env python
#coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
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
ANDROID_ACCESS_ID = 2100143172
ANDROID_ACCESS_TOKEN = '378a5775f37cf9c38f71b6df3e26fc56'#secret key
IOS_ACCESS_ID = 2200118927
IOS_ACCESS_TOKEN = '662a91c3bf96cc9e18111339764f22d2'
SCHEMA_PREFIX = 'faxian://'
IOS_ENV = 2

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
    def _push_single_device(self, device_id, msg, device_type, env=IOS_ENV):#xinge.XingeApp.ENV_DEV):#ios上线要修改成1
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

    #@timer('batch notify over')
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

    #@timer('single push called cost')
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

    #@timer('broadcast end')
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
        ios_msg = self._build_msg(notify, DeviceType.IOS)
        android_msg = self._build_msg(notify, DeviceType.ANDROID)
        if not ios_msg or not android_msg:
            logger.warning('msg[msg generate error]')
            return MSG_ERROR

        if send_time:
            ios_msg.sendTime = send_time
            android_msg.sendTime = send_time

        ret = None
        if device_type == DeviceType.ANDROID:
            ret = self.android_push_app.PushAllDevices(0, android_msg)
            logger.info('ret[%s]' % ret)
        if device_type == DeviceType.IOS:
            ret = self.ios_push_app.PushAllDevices(0, ios_msg, IOS_ENV)
            logger.info('ret[%s]' % ret)
        else:
            ret1 = self.android_push_app.PushAllDevices(0, android_msg)
            ret2 = self.ios_push_app.PushAllDevices(0, ios_msg, IOS_ENV)
            logger.info('ret1[%s], ret2[%s]' % (ret1, ret2))
            #ret = ret1 and ret2

        if ret:
            if ret[0] == 0:
                return SUCCESS
            else:
                return BROADCAST_ERROR

        return RET_UNKNOWN_ERROR

    def _del_tag(self, token_group):
        for dtype in token_group:
            for token in token_group[dtype]:
                result = ()
                if dtype == DeviceType.ANDROID:
                    result = self.android_push_app.QueryTokenTags(token)
                if dtype == DeviceType.IOS:
                    result = self.ios_push_app.QueryTokenTags(token)
                logger.info('msg[query tag] token[%s] result[%s]' % (token, result))

                tag_list = []
                if result[0] == 0:
                    tag_list = result[2]

                if tag_list:
                    tag_pair = [xinge.TagTokenPair(i, token) for i in tag_list]

                    if dtype == DeviceType.ANDROID:
                        result = self.android_push_app.BatchDelTag(tag_pair)
                    if dtype == DeviceType.IOS:
                        result = self.ios_push_app.BatchDelTag(tag_pair)

                    logger.info('msg[delete tag] token[%s] tag_pair[%s] result[%s]' % (token, tag_pair, result))

    def _get_condition_push_device(self, city, school, ukind_verify):
        limit = 5000
        offset  = 0
        while True:
            users = UserDetail.get_user(city, school, ukind_verify, offset, limit)
            if users == None:
                yield []
                break
            uid_list = [u.uid for u in users]
            logger.info("msg[get condition push] city[%s] school[%s] ukind_verify[%s] uid%s offset[%s] limit[%s]" % (city, school, ukind_verify, uid_list, offset, limit))
            device_infos = UserPush.get_device_list(uid_list)
            yield [(d.device_type, d.xg_device_token) for d in device_infos]
            if len(uid_list) < limit:
                break
            offset += limit

    #@timer('op tag end')
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

        if request.op == 1:
            self._del_tag(token_group)

        tag_list = request.tag_list
        tag_list.append('all_city')
        tag_list.append('all_school')

        for dtype in token_group:
            tag_token_list = []
            xg_device_token = token_group[dtype]
            for token in xg_device_token:
                if dtype == DeviceType.ANDROID:
                    UserPush.update_tags(token, ','.join(tag_list+['android']))
                    l = [xinge.TagTokenPair(x, token) for x in tag_list+['android']] 
                if dtype == DeviceType.IOS:
                    UserPush.update_tags(token, ','.join(tag_list+['ios']))
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

                if result[0] != 0:
                    logger.warning('msg[set tag error] tags[%s] uid[%s] tagpair[%s] op[%s] ret[%s]' % (tag_list, request.uid, l, request.op, result))


        return SUCCESS

    def _tag_push(self, tag_list, msg, device_type, push_task_id):#暂时没用上
        retry = 2
        ret = None
        for i in range(retry):
            if device_type == DeviceType.IOS:
                ret = self.ios_push_app.PushTags(0, tag_list, 'AND', msg, IOS_ENV)
            if device_type == DeviceType.ANDROID:
                ret = self.android_push_app.PushTags(0, tag_list, 'AND', msg)
            logger.info('msg[condition push result] retry[%s] device_type[%s] tags[%s] msg[%s] ret[%s] push_task_id[%s]' % (i, device_type, tag_list, msg, ret, push_task_id))
            if ret[0] == 0:
                return ret[2]

        return -1


    def condition_push(self, request):
        gevent.spawn(self._condition_push, request)
    
    def _condition_push(self, request):
        logger.info('msg[condition push begin] request[%s]' % request)
        verify_map = {'unverify': 0, 'verify': 1}

        notify = request.notify
        push_task_id = request.push_task_id


        city = request.city.split(',')
        school = request.school.split(',')
        ukind_verify = request.ukind_verify.split(',')

        task_list = []
        push_id_list = []
        i = 1
        for tag_list in itertools.product(city, school, ukind_verify):
            for device_list in self._get_condition_push_device(tag_list[0], tag_list[1], verify_map.get(tag_list[2], 0)):
                for device in device_list:
                    if request.device_type == device[0] or request.device_type == 0:
                        if device[0] == DeviceType.IOS:
                            ios_msg = self._build_msg(notify, DeviceType.IOS)
                            task_list.append(gevent.spawn(self._push_single_device, device[1], ios_msg, device[0]))
                        if device[0] == DeviceType.ANDROID:
                            android_msg = self._build_msg(notify, DeviceType.ANDROID)
                            task_list.append(gevent.spawn(self._push_single_device, device[1], android_msg, device[0]))
                        i+=1
            if i % 700 == 0:
                gevent.joinall(task_list, timeout=5)
                task_list = []
