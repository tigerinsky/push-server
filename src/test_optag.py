#coding:utf-8

#import handler.push_service_handler
from handler.push_service_handler import PushServiceHandler
from push.ttypes import *

request = TagRequest()

request.uid = 1
request.op = 1
request.tag_list = ['test1', 'test2', 'test3', '北京']

handler = PushServiceHandler()
handler.optag(request)

print handler.android_push_app.QueryTokenTags('a05944c46da3c2b24528831b12041322ad3ee66e')
