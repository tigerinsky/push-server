#coding:utf-8

#import handler.push_service_handler
from handler.push_service_handler import PushServiceHandler
from push.ttypes import *

notify = Notify()
notify.mtype = 1
notify.ltype = 1
notify.content = 'test'
notify.title = ''

request = ConditionPushRequest()
request.notify = notify
request.device_type = 1
request.city = 'all_city'
request.school = 'all_school'
request.ukind_verify = 'test1'

handler = PushServiceHandler()

print handler.condition_push(request)
