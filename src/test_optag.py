#coding:utf-8

#import handler.push_service_handler
from handler.push_service_handler import PushServiceHandler
from push.ttypes import *

request = TagRequest()

request.uid = 43
request.op = 1
request.tag_list = ['test1', 'test2', 'test3', '北京']

handler = PushServiceHandler()
#handler.optag(request)

print handler.android_push_app.QueryTokenTags('8cdada03a93446ef47df83da01870872822107dd')
print handler.ios_push_app.QueryTokenTags('6c5790e3ead9d3dbb6dac57c84f08dcb52a7817e8e1ecd1ee6babb5ceb4a19cf')
print handler.android_push_app.QueryPushStatus([u'38937289', u'38937290'])
print handler.ios_push_app.QueryPushStatus([u'38937289', u'38937290'])
