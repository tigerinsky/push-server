import sys
sys.path.append('gen-py')
from push import PushService
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.server import TNonblockingServer

from handler.push_service_handler import PushServiceHandler
from util.log import logger

handler = PushServiceHandler()
processor = PushService.Processor(handler)
#transport = TSocket.TServerSocket(port=9990)
transport = TSocket.TServerSocket(port=8998)
#tfactory = TTransport.TFramedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

#server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
#server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
#server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
server = TNonblockingServer.TNonblockingServer(processor, transport, None, pfactory)
server.setNumThreads(12)

logger.info('Starting the server...')
server.serve()
logger.info('done.')
