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
notify.content = "ios首页推送"

request = SingleNotifyRequest()

request.notify = notify

request.device_type = 2
#request.device_id = '51fbd091ee0cf35c1384259b9b9c446df6987f83db0507d4c9b6dba689e389a5'
request.device_id = '9952e67639162056606d1fdc95febc7888853145380aa13b69cfffbf924e8a59'

try:
    transport = TSocket.TSocket('localhost', 8998)
    transport = TTransport.TFramedTransport(transport)
    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    # Create a client to use the protocol encoder
    client = PushService.Client(protocol)

    # Connect!
    transport.open()
    print client.single_notify(request);
except Exception, e:
    print 'xxx%s' % e

