#coding:utf-8
import sys
sys.path.append('gen-py')
import time

from push import PushService
from push.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

def build_wap_notify():
    notify = Notify()
    notify.type = NotifyType.WAP
    notify.url = 'http://www.baidu.com'
    notify.content = '测试wap推送跳转'
    notify.title = 'title'
    return notify

def build_index_notify():
    notify = Notify()
    notify.type = NotifyType.INDEX
    notify.content = 'test index push'
    notify.title = 'title'
    return notify

def build_tweet_notify():
    notify = Notify()
    notify.type = NotifyType.COMMUNITY_DETAIL
    notify.tid = 13696
    notify.content = 'test tweet push'
    notify.title = 'title'
    return notify

def test_single_push(client, device_id, device_type, push_type):
    singleRequest = SingleNotifyRequest()
    singleRequest.device_id = device_id
    singleRequest.device_type = device_type
    if push_type == NotifyType.WAP:
        singleRequest.notify = build_wap_notify()
    if push_type == NotifyType.INDEX:
        singleRequest.notify = build_index_notify()
    if push_type == NotifyType.COMMUNITY_DETAIL:
        singleRequest.notify = build_tweet_notify()
    if push_type == NotifyType.FRIEND:
        pass
    if push_type == NotifyType.PRIVATE_MSG:
        pass
    if push_type == NotifyType.SYSTEM_MSG:
        pass

    client.single_notify(singleRequest)

def test_batch_push(client, device_id_list, device_type, push_type):
    btn = BatchNotifyRequest()
    btn.device_id_list = device_id_list
    notify  = Notify()
    notify.title = 'test'
    notify.content = '批量推送单测'
    notify.type = 1
    btn.notify = notify
    btn.device_type = device_type
    client.batch_notify(btn)

def test_admin_notify(client):
    adRequest = AdminNotifyRequest()
    adRequest.type = 2
    adRequest.flow = 1
    adRequest.from_uid = 15
    adRequest.to_uid = 2
    adRequest.mid = 200
    adRequest.ctime = int(time.time())

    client.admin_notify(adRequest)





try:
    transport = TSocket.TSocket('localhost', 8998)
    transport = TTransport.TFramedTransport(transport)
    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    # Create a client to use the protocol encoder
    client = PushService.Client(protocol)

    # Connect!
    transport.open()
    client.ping()
    '''
    device_id = '26fd06ec71f8c4183ed6bfe61b4e2fb0'
    #device_id_list = ['26fd06ec71f8c4183ed6bfe61b4e2fb0',]
    #device_id_list = ['9ba23ec0360e7a4540d4a514574c795906df2bec',]
    device_id_list = ['04742481a277210eb137486767566c9f95b8cdc0fc6d6363826bc61ef4569c26',]
    info = Info()
    info.type = 1
    info.num = 3
    batchinfo = BatchInfoRequest()
    batchinfo.device_id_list = device_id_list
    batchinfo.info = info
    batchinfo.device_type = DeviceType.IOS
    client.batch_info(batchinfo)
    notify = Notify()
    notify.type = NotifyType.WAP
    notify.url = 'http://www.baidu.com'
    #notify.content = '新年快乐!2.19'
    notify.content = '测试'

    notify.title = 'title'
    #request = BroadcastRequest()
    #request.notify = notify
    #client.broadcast(request)
    #print 'ping()'
    singleRequest = SingleNotifyRequest()
    #singleRequest.device_id = '6a25da539a4d1dd14ae58cc4d700e69cd1533824'
    singleRequest.device_id = '9ba23ec0360e7a4540d4a514574c795906df2bec'
    singleRequest.device_type = 1
    #singleRequest.device_id = '04742481a277210eb137486767566c9f95b8cdc0fc6d6363826bc61ef4569c26'
    #singleRequest.device_type = 2

    singleRequest.notify = notify
    client.single_notify(singleRequest)
    singleRequest.device_id = 'fe80d75d3a8c655e4ef79a623fd461f3410487c6'
    client.single_notify(singleRequest)
    '''
    #device_id = 'fe80d75d3a8c655e4ef79a623fd461f3410487c6'
    #device_id = '97088b24da9c445188069bfa5b44fdd2d497a418d3a9368ebc90196b6166f4e8'
    #device_id='8cdada03a93446ef47df83da01870872822107dd'
    device_id='9ba23ec0360e7a4540d4a514574c795906df2bec'
    #test_single_push(client, device_id, 1, NotifyType.INDEX)
    #test_single_push(client, device_id, 1, NotifyType.COMMUNITY_DETAIL)
    device_id = '8e25fcba2d6b2fbe4ca0b32f86a434765ea7f5f9'
    test_single_push(client, device_id, 1, NotifyType.WAP)
    device_id = '9ba23ec0360e7a4540d4a514574c795906df2bec'
    device_id = '8e25fcba2d6b2fbe4ca0b32f86a434765ea7f5f9'
    #test_single_push(client, device_id, 1, NotifyType.COMMUNITY_DETAIL)
    #test_admin_notify(client)
    '''
    device_id_list = ['f44ee11b0ac85be187eb12df597a948918be53936426ea77e03ab6dbcb80ad85', '0e0b4b0203f71a77dc134f152fc74304ec0a3128649f375651f78ca5aa1ae359', 'f790b1814af78db64e0704411da9cd05cb46bed80ded44d8f406a2ce39dd9c1a']
    for i in range(10):
        device_id_list = []
        for i in range(750):
            device_id_list.append('f790b1814af78db64e0704411da9cd05cb46bed80ded44d8f406a2ce39dd9c1a')
        pre = time.time()
        test_batch_push(client, device_id_list, 2, 11111111111)
        cost = (time.time() - pre) * 1000
        print 'cost: %s' % cost
    '''

except Exception, e:
    print '%s' % e
