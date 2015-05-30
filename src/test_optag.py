#coding:utf-8

#import handler.push_service_handler
from handler.push_service_handler import PushServiceHandler
from push.ttypes import *

request = TagRequest()

request.uid = 43
request.op = 1
request.tag_list = ['test1', 'test2', 'test3', '北京']

handler = PushServiceHandler()
handler.optag(request)

print handler.android_push_app.QueryTokenTags('8cdada03a93446ef47df83da01870872822107dd')
