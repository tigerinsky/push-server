#coding:utf-8

from handler.push_service_handler import PushServiceHandler
from push import PushService
from push.ttypes import *
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

notify = Notify()

notify.mtype = 1
notify.ltype = 1
notify.content = "只是测试，收到请忽略"

request = ConditionPushRequest()

request.notify = notify
import pdb
#pdb.set_trace()

request.device_type = 0
#request.city = "北京,上海"
request.city = 'all_city'
request.school = "all_school"
#request.school = "清华"
request.ukind_verify = "unverify"

try:
    transport = TSocket.TSocket('localhost', 8998)
    transport = TTransport.TFramedTransport(transport)
    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    # Create a client to use the protocol encoder
    client = PushService.Client(protocol)

    # Connect!
    transport.open()
    client.condition_push(request);
except Exception, e:
    print 'xxx%s' % e

