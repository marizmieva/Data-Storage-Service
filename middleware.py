import socket
import serve
import logging
import sys
import os
import pathlib

fh = logging.FileHandler('logfile.log')
logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.server')
logger.addHandler(fh)

ACCOUNT = "acc"
LOGIN = "login"
LOGOUT = "logout"

LIST = "list"

DOWNLOAD = "download"
UPLOAD = "upload"
DELETE = "delete"



client_port =  6000
chunk_size = 32


def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

class Socket:
    is_connected: bool
    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        #self.socket.bind((host, port))
    
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            is_connected = True;
        except:
            logger.error(f"{self.port} failed to connect in node")
            is_connected = False


class Client:
    is_connected: bool
    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        #self.socket.bind((host, port))
    def connect(self):
        try:
            self.socket.bind((self.host, self.port))
            logger.info(f"client connected to {port}")
            is_connected = True;
        except:
            logger.error(f"{self.port} failed to bind in client")
            is_connected = False
    
def get_ports():
    if (len(sys.argv) < 5):
        raise ValueError("NO COMMAND LINE ARGUMENTS FOUND")
    else:
        return [ int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]),int(sys.argv[4])]

class Middleware:
    def __init__(self, chunk_size):
        self.client_socket = socket.socket()

        self.ports = get_ports()
        self.host = socket.gethostname()
        self.data_nodes = [Socket(self.host, port) for port in self.ports]
        self.chunk_size = chunk_size // 4
        self.client = Client(self.host, client_port)
        connected_nodes = 0
        while (connected_nodes < 2) :
            for node in self.data_nodes:
                try:
                    node.connect()
                    logger.info(f"{node.port} bound successfully in middleware")
                    connected_nodes += 1
                except:
                    logger.warning(f"{node.port} didn't bind in middleware")
        
        
    
    def distribute_data(self, data):
        chunks = [data[y-self.chunk_size:y] for y in range(self.chunk_size, len(data)+self.chunk_size,self.chunk_size)]
        try:
            self.data_nodes[0].send(chunks[0] + chunks[2])
        except:
            pass
        try:
            self.data_nodes[1].send(chunks[1] + chunks[3])
        except:
            pass
        try:
            self.data_nodes[2].send(byte_xor(chunks[0], chunks[1]) + byte_xor(chunks[2], chunks[3]))
        except:
            pass
        try:
            self.data_nodes[3].send(byte_xor(chunks[2], chunks[1]) + byte_xor( chunks[0], byte_xor(chunks[2], chunks[3])))
        except:
             pass
    
    def from_client(self, file_name):
        pass

    def to_servers(self, file_name):
        pass


def main():
    connector = Middleware(32);

if __name__ == "__main__":
    main()