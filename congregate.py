"""
Reads and maintains config file
Starts paxos and congregate protocol instances
Autonomous congregate functions loop
Handles client requests


"""

import asyncio
import websockets
import logging
import ssl
import configparser
import sys
import hashlib
import time
from logging.config import fileConfig
from BPCon.protocol import BPConProtocol
from congregateProtocol import CongregateProtocol
from state import StateManager

FORMAT = '%(levelname)s [%(filename)s %(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)

fileConfig('logging_config.ini')
logger = logging.getLogger()
configFile = sys.argv[1] # TODO improve

def load_config():
    
    config = configparser.ConfigParser()
    config.read(configFile)

    conf = {}
    conf['ip_addr'] = config['network']['ip_addr']
    conf['port'] = int(config['network']['port'])

    conf['peerlist'] = []
    for key,val in config.items('peers'):
        wss = "wss://"+key+":"+val
        conf['peerlist'].append(wss) 
    
    conf['peer_certs'] = config['creds']['peer_certs']
    conf['certfile'] = config['creds']['certfile']
    conf['keyfile'] = config['creds']['keyfile']
    conf['peer_keys'] = config['creds']['peer_keys']

    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.load_cert_chain(certfile=conf['certfile'], keyfile=conf['keyfile'])
    conf['ssl'] = ctx
    conf['logger'] = logger

    conf['is_client'] = int(config['testing']['is_client'])
    return conf



class Congregate:
    def __init__(self):
        try:
            conf = load_config()
            self.state = StateManager()
            self.loop = asyncio.get_event_loop()
            self.bpcon = BPConProtocol(conf, self.state) 
            self.c = CongregateProtocol(self.loop, conf, self.bpcon)       
            self.paxos_server = websockets.serve(self.bpcon.main_loop, conf['ip_addr'], conf['port'], ssl=conf['ssl'])
            self.congregate_server = websockets.serve(self.c.main_loop, conf['ip_addr'], conf['port'] + 2, ssl=conf['ssl'])
            #self.web_server = websockets.serve(self.mainloop, conf['ip_addr'], conf['port'] + 1)
            self.loop.run_until_complete(self.paxos_server)
            self.loop.run_until_complete(self.congregate_server)
          

            if conf['is_client']:
                logger.debug("making request")
                self.loop.run_until_complete(self.c.make_2pc_request("X,key,value"))
                #x = 0
                #while x < 10:
                    
                   # self.db_request("P,{},hello{}".format(x,x))
                   # x += 1

        except Exception as e:
            logger.info(e)

    def db_request(self, msg):
        logger.debug("db commit initiated")
        self.c.make_bpcon_request(msg)

    def shutdown(self):
        print(self.bpcon.state.db.kvstore)
        self.paxos_server.close()
        self.congregate_server.close()
    
    def direct_msg(self, msg):
        msg_type = msg[0]
        if msg_type == '0':
        # 0 -> bpcon
            return "hello"
        elif msg_type == '1': #custom or https -> serve or register and pass to congregate
        # 1 -> db get
            return "hello"
        elif msg_type == '2': 
        # 2 -> congregate
            return "hello"
        # Client Request Handling

    def handle_db_request(self, request):
        # client request for data
        # route if necessary (manage for client)
        # verification of request and requestor permissions
        # self.db.get(k)
        pass

        

    @asyncio.coroutine
    def mainloop(self, websocket, path):
        try:
            input_msg = yield from websocket.recv()
            logger.debug("< {}".format(input_msg))
            output_msg = self.direct_msg(input_msg)
            if output_msg:
                yield from websocket.send(output_msg)
                #self.bmsgs.append(output_msg)
                
            else:
                self.logger.error("got bad input from peer")

            # adapt here

        except Exception as e:
            self.logger.error("mainloop exception: {}".format(e))




def start():
    try:
        c = Congregate()
        try:
            try:
                asyncio.get_event_loop().run_forever()
            except Exception as e:
                logger.debug(e)
        except KeyboardInterrupt:
            c.shutdown()
            print('done')
        finally:
            asyncio.get_event_loop().close()
    except Exception as e:
        logger.debug(e)

start()  

