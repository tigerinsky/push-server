#coding:utf-8

#import handler.push_service_handler
from handler.push_service_handler import PushServiceHandler
from push.ttypes import *


handler = PushServiceHandler()
handler.get_condition_push_device("北京", "中央美院", 0)
