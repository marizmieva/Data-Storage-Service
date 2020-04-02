import socket
import argparse
import os
import logging

import sys
from pathlib import Path

import util
from util import chunk_size

LOGIN = "login"
ACC = "acc"

DOWNLOAD = "download"
UPLOAD = "upload"
LOGOUT = "logout"
DELETE = "delete"
LIST = "list"

ID = 'id'
CLOSE = "close"
port =  6000
chunk_size = 64

fh = logging.FileHandler('logfile.log', 'w')
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('server')
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)



class Server:
    middleware_socket: socket.socket
    dir_path: str
    identity: str
    def __init__(self, csoc: socket.socket, dir_path: str, identity: str, chunk_size:int):

        self.middleware_socket = csoc
        self.dir_path = dir_path
        self.current_path = dir_path
        self.identity = identity
        self.chunk_size = chunk_size

    def create_account(self, username_password):
        
        dir_list = os.listdir(self.current_path)
        
        try:
            dir_list.index(f"{username_password}")
            return 2, ""

        except ValueError:
            os.mkdir(f"{self.current_path}/{username_password}")
            logger.debug(f'created a folder at {self.current_path}')
            return 1, f"{username_password}"


    def login(self, username_password: str):
        dir_list = os.listdir(self.current_path)
        try:
            dir_list.index(username_password)
            return 1, f"{self.dir_path}/{username_password}"
        except ValueError:
            return 2, self.current_path
        

    def list_acc(self):
        dir_list = os.listdir(self.current_path)
        stringy_dir_list = '\n'.join(dir_list)

        logger.info(f'{stringy_dir_list}')
        dir_list = util.cut_chunks(stringy_dir_list)

        for item in dir_list:
            util.send_message(self.middleware_socket, item, self.chunk_size)
            util.send_message(self.middleware_socket, item, self.chunk_size)
        print('---sent all directory---')
        util.send_message(self.middleware_socket, (util.stop_phrase).decode('utf-8'), self.chunk_size)


    def server_protocol(self):

        logged_in = False
        first_empty_data_received = True
        empty_data_count = 0
        while True:
            if first_empty_data_received:
                print('waiting for instructions...')
            
            data = util.get_instructions(self.middleware_socket, self.chunk_size)

            if (len(data) == 0):
                empty_data_count += 1
                if first_empty_data_received:
                    logger.error(f'in {self.current_path}: data: {data} type {type(data)} len {len(data)}')
                
                if empty_data_count > 4:
                    break
                first_empty_data_received = False
                continue

            else:
                first_empty_data_received = True
                empty_data_count = 0

            if data.find(' ') > -1:
                command, username_password = str(data).split()
                logger.debug(f"in {self.current_path}: received {command} and {username_password}")
            else:
                command = str(data)
                logger.debug(f'in {self.current_path}: received {command} type of command {type(command)}')

            if command == ID:
                util.send_message(self.middleware_socket, self.identity, self.chunk_size)
                continue
            elif command == CLOSE:
                return True

            elif command == LOGOUT:
                logged_in = False
                self.current_path = self.dir_path
                continue

            if logged_in == False:
                if command == LOGIN:
                    result, self.current_path = self.login(username_password)

                    if (self.current_path != self.dir_path):
                        
                        util.send_message(self.middleware_socket, result, self.chunk_size)
                        logged_in = True
                        continue
                    else:
                        util.send_message(self.middleware_socket, result, self.chunk_size)
                        continue

                elif command == ACC:
                    
                    result, self.current_path = self.create_account(username_password)
                    if self.current_path != self.dir_path:
                        # account creation is successful
                        util.send_message(self.middleware_socket, '1', self.chunk_size) 
                        
                    else:
                        # account creation is not successful
                        util.send_message(self.middleware_socket, '2', self.chunk_size)
                else: 
                    # command is unknown
                    util.send_message(self.middleware_socket, '-1', self.chunk_size)
                    continue 

            elif logged_in == True:
                if command == DELETE:
                    try:
                        os.remove(f'{self.current_path}/{username_password}')
                        logger.info(f"{self.current_path}/{username_password}' removed successfully")
                        
                    except FileNotFoundError:
                        logger.error(f"{self.current_path}/{username_password}' DNE")
                        
                elif command == LIST:
                    logger.debug(f'got to {command}')
                    self.list_acc()

                elif command == UPLOAD:
                    util.receive_file(self.middleware_socket, f'{self.current_path}/{username_password}', self.chunk_size)

                elif command == DOWNLOAD:
                    util.send_file(self.middleware_socket, f'{self.current_path}/{username_password}', self.chunk_size)

                else:
                    logger.info(f'{self.middleware_socket} invalid command {command}, {self.chunk_size}')

def main():
    chunk_size = 64
    logger.info(f'\nsys.argv = {sys.argv}\n')
    if len(sys.argv) > 1:
        identity = sys.argv[1]
        os.makedirs(identity, exist_ok=True)
        dir_path = str(Path.cwd()) + '/' + identity
        
    else:
        raise ValueError("STORAGE NODE NOT IDENTIFIED")

    if len(sys.argv) > 2:
        logger.info(f'\nPort = {sys.argv[2]}\n')
        port = int(sys.argv[2])
    else:
        raise ValueError(f"PORT FOR NODE {identity} IS NOT IDENTIFIED")

    if len(sys.argv) > 3:
        chunk_size = int(sys.argv[3])
    else:
        logger.info(f"defaulting to chunk size {chunk_size}")
    while True:
        s = socket.socket()             # Create a socket object
        host = socket.gethostname()     # Get local machine name
        s.bind((host, port))            # Bind to the port
        s.listen(5)                     # Now wait for client connection.

        print  ('Server listening....')

        while True:
            s.listen(5)
            conn, addr = s.accept()     # Establish connection with client.
            print('Got connection from', addr)

            data_storage_node = Server(conn, dir_path, identity, chunk_size)
            told_to_close = data_storage_node.server_protocol()
            if told_to_close:
                print('---ending operation...---')
                break
            else:
                print('---restarting---')
                continue
    conn.close()



if __name__ == "__main__":
    main()