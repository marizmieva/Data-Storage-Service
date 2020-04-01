import socket
import util
import logging
import sys
import os
import pathlib as pl
from typing import List
import util

import random
from util import chunk_size


fh = logging.FileHandler('logfile.log')
logging.basicConfig(level=logging.DEBUG, filemode = "w")
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.middleware')
logger.addHandler(fh)

ACCOUNT = "acc"
LOGIN = "login"
LOGOUT = "logout"

LIST = "list"

DOWNLOAD = "download"
UPLOAD = "upload"

DELETE = "delete"
CLOSE = "close"

IDENTITY = 'id'
client_port =  6000

def test_assembly():
    a = b = 0
    while a == b:
        a = random.randint(0, 3)
        b = random.randint(0, 3)
    
    if a > b:
        return b, a
    else:
        return a, b


class Node:
    is_connected: bool
    socket: socket.socket
    host: int 
    port: int 
    server_id: str
    #name:str

    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.is_connected = False
        self.chunk_size = chunk_size
        
    
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.server_id = self.name()
        except:
            self.is_connected = False

    def name(self):
        util.send_message(self.socket, IDENTITY, self.chunk_size)
        self.server_id = util.get_instructions(self.socket, self.chunk_size)
        
        #throwaway = util.get_instructions(self.socket, self.chunk_size)

        #logger.debug(f'throwaway chunk = {throwaway}')
        return self.server_id


def get_ports():
    if (len(sys.argv) < 5):
        raise ValueError("NO COMMAND LINE ARGUMENTS FOUND")
    else:
        return [int(i) for i in sys.argv[1:]]

class Middleware:
    port: int
    host: int 
    chunk_size: int
    path: str
    directory: List[str]
    client_socket: socket.socket
    client_port: int
    def __init__(self):

        self.ports = get_ports()
        self.host = socket.gethostname()
        self.chunk_size = chunk_size
        self.path = str(os.getcwd())
        self.directory = []

        self.data_nodes = [Node(self.host, port) for port in self.ports[:-1]]
        self.client_port = self.ports[-1]
        iteration_count = 0
        connected_nodes = 0
        while (connected_nodes <= 4 and iteration_count < 4):  # 4 is picked arbitrarily
            iteration_count += 1
            for node in self.data_nodes:
                try:
                    node.connect()
                    connected_nodes += 1
                except:
                    logger.error(f"{node.port} didn't bind in middleware")
        

    def list_all(self, client_connection):
        chunk = b''

        util.send_message(self.data_nodes[0].socket, 'list', self.chunk_size)
        chunk = util.get_instructions(self.data_nodes[0].socket, self.chunk_size)

        if chunk == '-1':
                print('something went wrong')
                return False

        while chunk.find(util.stop_phrase.decode("utf-8")) == -1:
            util.send_message(client_connection, chunk, self.chunk_size)

            self.directory.append(chunk)
            chunk = util.get_instructions(self.data_nodes[0].socket, self.chunk_size)
            if chunk == '-1':
                print('something went wrong')
                return False
        util.send_message(client_connection, util.stop_phrase.decode("utf-8"), self.chunk_size)

    def create_account(self, connection, command):
        username, password = (util.get_instructions(connection, self.chunk_size, False)).split()
        #util.send_message(connection, 'welcome', self.chunk_size)
        logged_in = 0
        for node in self.data_nodes:
            data = f"{command} {username}-{password}"
            logger.debug("Data: " + data)

            util.send_message(node.socket, data, self.chunk_size)

            response = util.get_instructions(node.socket, self.chunk_size)

            print(f'\n\n response is {response} len of resp is {len(response)}')
            if response == '1':
                util.send_message(connection, 'welcome', self.chunk_size)
                logged_in += 1
                
            elif response == '2':
                util.send_message(connection, 'error: account already exists, try a different username or login', self.chunk_size)
            
            elif response == '-1':
                util.send_message(connection, 'something went wrong', self.chunk_size)
        
        return logged_in == len(self.data_nodes)
                


    def login(self, client_connection):
        credentials = util.get_instructions(client_connection, self.chunk_size)
        #print(f'got credentials {credentials}')
        try: 
            username, password = credentials.split()
        except:
            username = -1
            password = -1

        if username == -1:
            return False

        logged_in = 0

        for node in self.data_nodes:
            util.send_message(node.socket, f'login {username}-{password}', self.chunk_size)

            result = util.get_instructions(node.socket, self.chunk_size)
            logger.debug(f'answer from server {node.host} is {result} type of result is {type(result)}')
            if result == '1':
                logged_in += 1
        
        if logged_in == len(self.data_nodes):
            util.send_message(client_connection, 'welcome', self.chunk_size)
            return True 
        else:
            util.send_message(client_connection, 'failed to log in', self.chunk_size)
            return False


    def delete_file(self, filename):
        result = 0
        for node in self.data_nodes:
            util.send_message(node.socket, f'{DELETE} {filename}', self.chunk_size)
        return result == len(self.data_nodes)


    def run_protocol(self, client_connection):
        logged_in = False
        while True:
        #    self.directory = self.list_all(client_connection)
            print('waiting for instructions...')
            data = util.get_instructions(client_connection, self.chunk_size)

            logger.debug(f"Received data from get_instructions: {data}")
            if data == CLOSE:
                client_connection.close()
                return True
            if data == LOGOUT:
                for node in self.data_nodes:
                    util.send_message(node.socket, LOGOUT, self.chunk_size)
                logged_in = False
                continue

            if not logged_in:
                if data.find(LOGIN) > -1:
                    #self.list_all(client_connection, False)
                    logged_in = self.login(client_connection)
                    if logged_in:
                        #self.list_all(client_connection, False)
                        logger.info('successful login')
                    else:
                        logger.info('failed to log in')
                elif data.find(ACCOUNT) > -1:
                
                    logged_in = self.create_account(client_connection, data)

                else:
                    util.send_message(client_connection, 'login or acc to create an account', self.chunk_size)
            else:
                commands = data.split()
                if len(commands) < 2:
                    if commands[0] == LIST:
                        result = self.list_all(client_connection)
                    else:
                        logger.debug(f'{client_connection}, wrong command {commands}, {self.chunk_size}')

                    
                elif len(commands) == 2:
                    command, filename = commands[0], commands[1]
                    if command ==  DOWNLOAD:
                        result = self.assemble_data(client_connection, filename)
                        print('------downloaded------')
                    elif command == UPLOAD:
                        self.to_servers(client_connection, filename)
                        print('-------uploaded-------')

                    elif command == DELETE:
                        result = self.delete_file(filename)
                        continue
                    else:
                        # TODO: handle wrong command without writing it into file: 
                        # send stop phrase padded with 'wrong message
                        logger.debug(f'{client_connection}, wrong command {command}, {self.chunk_size}')

    
    def distribute_data(self, data:bytes, final_chunk=False):
        '''
        nodeA = chunk0 + chunk2
        nodeB = chunk1 + chunk3
        nodeC = chunk0 xor chunk1 + chunk2 xor chunk3
        nodeE = chunk2 xor chunk1 + chunk0 xor (chunk3 xor chunk3)
        '''
        # chunks = [(data[i], data[i + 1], data[i + 2 ]
        # chunk_range = range(self.chunk_size, len(data) + self.chunk_size, self.chunk_size)
        # chunks = [data[y-self.chunk_size:y] for y in chunk_range]
        # connected_count = 0
        
        ##data = 
        print('distribute data ')
        if final_chunk:
            chunks = util.process_chunks(data, chunk_size)
        else:
            chunks = util.cut_chunks(data)

        logger.debug(f'chunks prepared: {chunks}')

        (self.data_nodes[0].socket).sendall(chunks[0] + chunks[2])
        logger.debug(f'A xor B node')
        (self.data_nodes[1].socket).sendall(chunks[1] + chunks[3])
        logger.debug(f'A xor C node')
        (self.data_nodes[2].socket).sendall(util.xor(chunks[0], chunks[1]) + util.xor(chunks[2], chunks[3]))
        logger.debug(f'A xor D node')
        (self.data_nodes[3].socket).sendall(util.xor(chunks[2], chunks[1]) + util.xor(chunks[0], util.xor(chunks[2], chunks[3])))
        logger.debug(f'B xor d node')
        return 
    
    def to_servers(self, client_connection, filename):
        # TODO: after fixing padding broke upload
        '''
        * downloads file to the middleware folder
        * uses distribute data to split and xor items into chunks for storage
        * makes sure that the file contains a number of chunks divisible by 4
        * sends files to the storage nodes
        '''
        if not os.path.exists('middle'):
            os.mkdir('middle')
        got_chunks_to_middle = util.receive_file(client_connection, f'middle/{filename}', self.chunk_size)
        print (f'downloaded chunks: {got_chunks_to_middle}')
        
        for node in self.data_nodes:
            util.send_message(node.socket, f'{UPLOAD} {filename}', self.chunk_size)
        # login, run, foxy, download ch11.txt
        with open(f'middle/{filename}', 'rb') as f:
            buffer = f.read(4 * self.chunk_size)
            last_buffer = f.read(4 * self.chunk_size)
            while last_buffer:
                self.distribute_data(buffer)
                buffer = last_buffer
                last_buffer = f.read(4 * self.chunk_size)
            self.distribute_data(buffer, final_chunk=True)

        terminating_sequence = (util.stop_phrase).decode('utf-8')
        terminating_chunk = f'0{terminating_sequence}'
        for node in self.data_nodes:
            util.send_message(node.socket, terminating_chunk, self.chunk_size)
        return True
        #while len(buffer) == 4*self.chunk_size
        

    def find_nodes(self):
        identities = ""
        nodes = []
        count = 0

        for node in self.data_nodes:
            identities += node.server_id
            nodes.append(node.socket)
            count += 1
            if count == 2:
                return nodes, identities

    def assemble_data(self, client_connection, file_name):
        '''
        1. AB <= nodeA[0] + nodeB[0] + nodeA[1] + nodeB[1]
        
        2. AC <= nodeA[0] + xor(nodeC[0], nodeA[0]) + nodeB[1] + xor(nodeC[1], nodeA[1]) + 

        3. AD <= nodeA[0] + xor(nodeD[0], nodeA[1]) + nodeA[1], xor(xor(nodeD[1], nodeA[0]), nodeA[1])

        4. BC <= xor(nodeC[0], nodeB[0]) + nodeB[0] + xor(nodeC[1], nodeB[1]) + nodeB[1]

        5. BD <= ii + i + iii + iv
            i   B[0] = xor(nodeD[0], nodeC[0])
            ii  A[0] = xor(nodeD[1], xor(nodeB[1], B[0]])
            iii A[1] = nodeB[0]
            iv  B[1] = nodeB[1]
        
        6. CD <= xor(nodeD[1], nodeC[1]) + 
            i   A[0] = xor(nodeD[1], nodeC[1])
            ii  A[1] = xor(nodeC[0], A[0])
            iii B[0] = xor(nodeD[0], A[1])
            iv  B[1] = xor(nodeC[1], B[0])
        '''
        # randomizes servers that you use for file download
        n1, n2 = test_assembly()
        # hardcoded servers A&B as they are the easiest ones to assemble data from
        # n1, n2 = 0, 1
        
        if self.data_nodes[n1].server_id > self.data_nodes[n2].server_id:
            swap = n1
            n1 = n2
            n2 = swap

        file_one = f'middle/{file_name}{self.data_nodes[n1].server_id}'
        file_two = f'middle/{file_name}{self.data_nodes[n2].server_id}'

        identities = self.data_nodes[n1].server_id + self.data_nodes[n2].server_id
        nodes = [self.data_nodes[n1].socket, self.data_nodes[n2].socket]

        util.send_message(nodes[0], f'download {file_name}', self.chunk_size)

        file_one_counter = util.receive_file(self.data_nodes[n1].socket, file_one, self.chunk_size)

        util.send_message(nodes[1], f'download {file_name}', self.chunk_size)

        file_two_counter = util.receive_file(self.data_nodes[n2].socket, file_two, self.chunk_size)

        logger.debug(f"Starting to assemble data using identities={identities}")
        if identities == "AB":
            util.assembleAB(nodes, file_one, file_two)

        elif identities == "AC":
            util.assembleAC(nodes, file_one, file_two)

        elif identities == "AD":
            util.assembleAD(nodes, file_one, file_two)

        elif identities == "BC":
            util.assembleBC(nodes, file_one, file_two)

        elif identities == "BD":
            util.assembleBD(nodes, file_one, file_two)

        elif identities == 'CD':
            util.assembleCD(nodes, file_one, file_two)

        else:
            logger.error(f'{identities} is not a valid combination')
            util.send_message(self.client_socket.socket, 'servers failed. sorry :(', self.chunk_size)
            return False
        
        full_file_path = str((pl.Path("middle") / file_name).absolute())
        util.send_file(client_connection, full_file_path, self.chunk_size)
        

def main():
    
    while True:
        connector = Middleware()
        server_socket = socket.socket()
    
        if len(sys.argv) > 4:
            client_port = int(sys.argv[-1]) 
    
        server_socket.bind((socket.gethostname(),client_port))

        server_socket.listen(5)

        client_connection, client_addr = server_socket.accept()
        print ( f'accepted connection from {client_addr}, port {client_connection}, {client_port}')
        
        told_to_exit = connector.run_protocol(client_connection) 
        if not told_to_exit:
            print('restarting operation...')
        else:
            print('---exit---')
            return told_to_exit
    return told_to_exit


if __name__ == "__main__":
    main()

