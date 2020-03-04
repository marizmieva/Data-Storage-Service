import socket
import serve
import logging

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('tcpserver')


class Socket:
    is_connected: bool

    def __init__(self, name, shift, host, port, count):
        self.socket = socket.socket()
        # self.socket.bind((host, port + shift + count))
    
    def bind(self, shift):
        self.socket.bind((host, port + shift + count))


DATA_NODES_NAMES = ["A", "B", "AB", "BA"]

class Middleware:
    def __init__(self, port, chunk_size):
        self.sockets
        self.client_socket = socket.socket()
        self.data_nodes = [Socket(DATA_NODES_NAMES[i], i) for i in DATA_NODES_NAMES]
        host = socket.gethostname()
        
        
        error_shift = 0
        connected_nodes = 0
        while (connected_nodes < 2):
            for node in self.data_nodes:
                try:
                    node.bind()
                    logger.info(f"{node.name} bound successfully")
                    connected_nodes += 1
                except:
                    logger.warning(f"{node.name} didn't bind")
                

            