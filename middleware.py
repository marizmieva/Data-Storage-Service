import socket
import util
import logging
import sys
import os
import pathlib as pl
from typing import List
import util
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

IDENTITY = 'id'
client_port =  6000
chunk_size = 32




class Node:
    is_connected: bool
    socket: socket.socket
    host: int 
    port: int 
    #name:str

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

    def name(self):
        util.send_message(self.socket, IDENTITY)
        identity = socket.recv(8)
        return identity.decode("utf-8")



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
        self.client_port = self.ports[-1]
        self.chunk_size = chunk_size // 4
        self.path = str(os.getcwd())
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
        temp_socket.bind(self.host, self.ports[-1])
        logger.info(f'established a client socket')
        return temp_socket

    def connect_to_client(self):
        connection.listen(5)
        logger.info(f'listening for client socket')

    def list_all(self):
        chunk = b''
        chunk = util.get_instructions(self.data_node[0].socket, self.chunk_size, False, False)
        while chunk.find(util.stop_phrase.encode("utf-8")) == -1:
            util.send_message(connection, chunk)
            self.directory.append(chunk.decode('utf-8'))
            chunk = util.get_instructions(self.data_node[0].socket, self.chunk_size, False, False)

    def create_credentials(self, connection):
        util.send_message(connection, 'username:')
        username = util.get_instructions(connection, self.chunk_size)
        
        while not passwords_match:
            util.send_message(connection, 'password:')
            password = util.get_instructions(connection, self.chunk_size)
            
            repeat_password = get_instruction(connection, self.chunk_size)

            if password == repeat_password:
                return usename, password
            else:
                util.send_message(connection, 'passwords don\'t match, try again')
                continue
    
    def create_account(self, connection):
        username, password = self.create_credentials()
        util.send_message(connection, 'welcome')
        for node in self.data_nodes:
            node.socket.sendall(f"{command} {username} {password}".encode("utf-8"))
            response = node.socket.recv(self.chunk_size)
            if response == b'1':
                util.send_message(connection, 'welcome')
                return True
            elif response == b'2':
                util.send_message(connection, 'error: account already exists, try a different username or login')
                return False
            else:
                util.send_message(connection, 'something went wrong')
                return False

    def get_credentials(self, connection):
        util.send_message(connection, 'username:')
        username = util.get_instructions(connection, self.chunk_size)

        util.send_message(connection, 'password:')
        password = util.get_instructions(connection, self.chunk_size)
        return username, password

    def login(self, connection):
        username, password = self.get_credentials()

        if self.directory.find(f'{username}-{password}') > -1:
            for node in self.data_nodes:
                util.send_message(node.socket, f'login {username} {password}')
                result = util.get_instructions(node.socket)
                if result == b'1':
                    continue
                else:
                    print('error logging in')
            util.send_message(connection, 'welcome')
            return True 
        else:
            util.send_message(connection, f'incorrect usename or password')
        return False

    def to_server(self, filename):
        size = os.path.getsize(self.path + filename)
        f = open(filename, 'rb')
        buffer = f.read(4 * (self.chunk_size))
        while len(buffer) == 4*self.chunk_size:
            self.distribute_data(buffer)
            buffer = f.read(4 * (self.chunk_size))

    def from_server(self, filename):
        pass


    def run_protocol(self):
        logged_in = False
        connected = False

        while True:
            if not connected:
                self.client_socket.listen(5)
                connection, addr = temp_socket.accept()
                print(f"got connection from {addr}")
                connected = True
                connection.util.send_message("enter acc, to create an account or login to log in")
            else:
                self.directory = list_all()
                connection.util.send_message("enter a command")
                data = connection.recv(32)
                data = util.get_instructions(connection, self.chunk_size)

                if data == CLOSE:
                    connection.close()
                    self.client_socket = make_client_socket()
                    connected = False
                    continue

                if not logged_in:
                    if data == LOGIN:
                        logged_in = self.login()
                    elif data == ACC:
                        logged_in = self.create_account()
                    else:
                        util.send_message(connection, 'login or acc to create an account')
                else:
                    commands = data.split()
                    if len(commands) < 2:
                        if commands[0] == LIST:
                            self.list_files(connection)
                        else:
                            util.send_message(connetion, f"wrong command {data}")
                    elif len(commands) == 2:
                        command, filename = commands[0], commands[1]
                        if command ==  DOWNLOAD:
                            result = self.from_server(filename, connection)
                        elif command == UPLOAD:
                            result = self.to_server(filename, connection)
                        elif command == DELETE:
                            result = self.delete_file(filename)
                        else:
                            util.send_message(f'wrong command {data}')

    
    def distribute_data(self, data):
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
                self.data_nodes[2].socket.send(util.xor(chunk[0], chunk[1]) + util.xor(chunk[2], chunk[3]))
            except:
                connected_count += 1
            try:
                self.data_nodes[3].socket.send(util.xor(chunk[2], chunk[1]) + util.xor(chunk[0], util.xor(chunk[2], chunk[3])))
            except:
                connected_count += 1

        if connected_count < 2:
            logger.error('something is wrong with data distribution')
        return padded_zeroes_count

    
    def assemble_data(self):
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
        count = 0
        identities = ""
        nodes = []
        for node in self.data_nodes:
            if node.is_connected:
                identities += node.name()
                nodes.append(node)
            count += 1
            if count == 2:
                break

        file_one = util.receive_file(nodes[0].socket, file_name, self.chunk_size, file_name + identities[0])
        file_two = util.receive_file(nodes[1].socket, file_name, self.chunk_size,file_name + identities[1])

        if identities == "AB":
            util.assembleAB(file_name + identities[0], file_name + identities[1])

        elif identities == "AC":
            util.assembleAC(file_name + identities[0], file_name + identities[1])

        elif identities == "AD":
            util.assembleAD(file_name + identities[0], file_name + identities[1])

        elif identities == "BC":
            util.assembleBC(file_name + identities[0], file_name + identities[1])

        elif identities == "BD":
            util.assembleBD(file_name + identities[0], file_name + identities[1])

        elif identities == 'CD':
            util.assembleCD(file_name + identities[0], file_name + identities[1])

        else:
            logger.error(f'{identities} is not a valid combination')
            util.send_message(self.client_socket.socket, 'servers failed. sorry :(')


def main():
    connector = Middleware(32)
    connector.run_protocol()

if __name__ == "__main__":
    main()