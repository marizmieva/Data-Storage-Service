import socket
import util
import logging
import sys
import os
import pathlib as pl
from typing import List
from util import send_file, send_message, receive_file, is_accessible, stop_phrase, byte_xor
from getpass import getpass


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
CLOSE = "close"
client_port =  6000
chunk_size = 32




class Node:
    is_connected: bool
    socket: socket.socket
    host: int 
    port: int 
    name:str

    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.name
        #self.socket.bind((host, port))
    
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            is_connected = True;
        except:
            logger.error(f"{self.port} failed to connect in node")
            is_connected = False

    def get_name(self):
        pass


def get_ports():
    if (len(sys.argv) < 5):
        raise ValueError("NO COMMAND LINE ARGUMENTS FOUND")
    else:
        return [ int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]),int(sys.argv[4]), int(sys.argv[5])]


class Middleware:
    port: int
    host: int 
    chunk_size: int
    path: str
    directory: List[str]
    client_socket: socket.socket
    client_port: int
    def __init__(self, chunk_size):

        self.ports = get_ports()
        self.host = socket.gethostname()
        self.data_nodes = [Node(self.host, port) for port in self.ports[:-1]]
        self.client_port = ports[-1]
        self.chunk_size = chunk_size // 4
        self.path = os.getcwd()
        iteration_count = 0
        connected_nodes = 0
        while (connected_nodes < 2 and iteration_count < 4):  # 4 is picked arbitrarily
            for node in self.data_nodes:
                try:
                    node.connect()
                    logger.info(f"{node.port} bound successfully in middleware")
                    connected_nodes += 1

                except:
                    logger.warning(f"{node.port} didn't bind in middleware")
            iteration_count += 1
        if iteration_count == 4:
            raise Exception("We were unable to connect to all data nodes")
        self.client_socket = self.make_client_socket()

    def make_client_socket(self):
        temp_socket = socket.socket()
        temp_socket.bind(self.host,)
        logger.info(f'established a client socket')
        return temp_socket
    
    def await_connection(self):
        pass

    def connect_to_client(self):
        connection.listen(5)
        logger.info(f'listening for client socket')

    def list_all(self):
        chunk = b''
        chunk = get_instructions(self.data_node[0].socket, self.chunk_size, False, False)
        while chunk.find(stop_phrase) == -1:
            send_message(connection, chunk)
            self.directory.append(chunk.decode('utf-8'))
            chunk = get_instructions(self.data_node[0].socket, self.chunk_size, False, False)

    def create_credentials(self, connection):
        send_message(connection, 'username:')
        username = get_instructions(connection, self.chunk_size)
        
        while not passwords_match:
            send_message(connection, 'password:')
            password = get_instructions(connection, self.chunk_size)
            
            repeat_password = get_instruction(connection, self.chunk_size)

            if password == repeat_password:
                return usename, password
            else:
                send_message(connection, 'passwords don\'t match, try again')
                continue
    
    def create_account(self, connection):
        username, password = self.create_credentials()
        send_message(connection, 'welcome')
        for node in self.data_nodes:
            node.socket.sendall(f"{command} {username} {password}".encode("utf-8"))
            response = node.socket.recv(self.chunk_size)
            if response == b'1':
                send_message(connection, 'welcome')
                return True
            elif response == b'2':
                send_message(connection, 'error: account already exists, try a different username or login')
                return False
            else:
                send_message(connection, 'something went wrong')
                return False

    def get_credentials(self, connection):
        send_message(connection, 'username:')
        username = get_instructions(connection, self.chunk_size)

        send_message(connection, 'password:')
        password = get_instructions(connection, self.chunk_size)
        return username, password

    def login(self, connection):
        username, password = self.get_credentials()

        if self.directory.find(f'{username}-{password}') > -1:
            for node in self.data_nodes:
                send_message(node.socket, f'login {username} {password}')
                result = get_instructions(node.socket)
                if result == b'1':
                    continue
                else:
                    print('error logging in')
            send_message(connection, 'welcome')
            return True 
        else:
            send_message(connection, f'incorrect usename or password')
        return False

    def enter(self):
        logged_in = False
        connected = False

        connection.send_message("enter acc, to create an account or login to log in")
        
        while True:
            if not connected:
                self.client_socket.listen(5)
                connection, addr = temp_socket.accept()
                print(f"got connection from {addr}")
                connected = True
            else:
                self.directory = list_all()
                connection.send_message("enter a command")
                data = connection.recv(32)
                data = get_instructions(connection, self.chunk_size)

                if data == CLOSE:
                    connection.close()
                    self.client_socket = make_client_socket()
                if not logged_in:
                    if data == LOGIN:
                        logged_in = self.login()
                    elif data == ACC:
                        logged_in = self.create_account()
                    else:
                        send_message(connection, 'login or acc to create an account')
                else:
                    
                    if data ==  DOWNLOAD:
                        pass
                    elif data == UPLOAD:
                        pass
                    elif data == DELETE:
                        pass


        

    def distribute_data(self, data):
        '''
        nodeA = chunk0 + chunk2
        nodeB = chunk1 + chunk3
        nodeC = chunk0 xor chunk1 + chunk2 xor chunk3
        nodeE = chunk2 xor chunk1 + chunk0
        '''
        # chunks = [(data[i], data[i + 1], data[i + 2 ]
        # chunk_range = range(self.chunk_size, len(data) + self.chunk_size, self.chunk_size)
        # chunks = [data[y-self.chunk_size:y] for y in chunk_range]
        # connected_count = 0
        chunks, padded_zeroes_count = make_chunks(data, self.chunk_size)
        for chunk in chunks:
            connected_count = 0
            try:
                self.data_nodes[0].socket.send(chunk[0] + chunk[2])
            except:
                connected_count += 1
            try:
                self.data_nodes[1].socket.send(chunk[1] + chunk[3])
            except:
                connected_count += 1
            try:
                self.data_nodes[2].socket.send(byte_xor(chunk[0], chunk[1]) + byte_xor(chunk[2], chunk[3]))
            except:
                connected_count += 1
            try:
                self.data_nodes[3].socket.send(byte_xor(chunk[2], chunk[1]) + byte_xor(chunk[0], byte_xor(chunk[2], chunk[3])))
            except:
                connected_count += 1

        if connected_count < 2:
            raise Exception("error distributing data between storage nodes")
    

    def wait_for_client(self):
        
        self.client_socket.listen(5)
        logger.info(f"{self.client_socket} is listening...")
        

        while True: 
            connection, address = self.client_socket.accept()
            logger.info(f"got connection from {address}")
            interaction_client(connection)

            connection.send("over")
            connection.close()

    
        


def make_chunks(data, chunk_size):
    number_of_full_chunks = data // chunk_size
    chunks = []
    # Append data
    for i in range(number_of_full_chunks):
        chunks.append([data[i + byte_index] for byte_index in range(chunk_size)])
    leftover_bytes = []
    # Append leftover bytes
    for leftover_byte_index in range(data % chunk_size):
        leftover_bytes.append(data[number_of_full_chunks + leftover_byte_index])
    padded_zeroes_count = 0
    while (leftover_bytes and len(leftover_bytes) < chunk_size):
        leftover_bytes.append(b'0')
        padded_zeroes_count += 1
    if leftover_bytes:
        chunks.append(leftover_bytes)
    # Append padded chunks to make chunk count % 4 == 0
    while len(chunks) % 4 != 0:
        chunks.append([b'0'] * chunk_size)
        padded_zeroes_count += 1
    return chunks, padded_zeroes_count

def main():
    connector = Middleware(32);

if __name__ == "__main__":
    main()