import socket
import argparse
import os
import logging

import sys
from pathlib import Path

from getpass import getpass

from util import chunk_size


import util

logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.server')


LOGIN = "login"
ACC = "acc"
DOWNLOAD = "download"
UPLOAD = "upload"
LOGOUT = "logout"
DELETE = "delete"
LIST = "list"

CLOSE = "close"

fh = logging.FileHandler('logfile.log')
logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.client')
logger.addHandler(fh)


class Client:
    is_connected: bool
    
    def __init__(self,  client_socket: socket.socket):
        self.dir_path = 'client_dir'

        if not os.path.exists(self.dir_path):
            os.mkdir(self.dir_path)
        
        self.socket = client_socket
        self.chunk_size = chunk_size
    
    def _login(self):
        username = input('username >> ')
        password = getpass('password >> ')
        util.send_message(self.socket, f'{username} {password}', self.chunk_size)

        instructions = util.get_instructions(self.socket, self.chunk_size)

        logger.debug(f'command received by client is {instructions}')
        if instructions == 'welcome':
            return True
        else: 
            return False

    def create_credentials(self):
        
        while True:
            password = getpass('>> ')
        
            password2 = getpass('repeat password:\n>> ')
            
            if password == password2:
                return password
            else: 
                continue


    def create_account(self):
        counter = 0
        password2, password, username = '', '', ''
        while counter <= 5:
            
            while counter <= 5 and (len(username) < 2 or username.find(' ') > -1 ):
                print('username must be at least 2 characters. no spaces')
                username = input('username\n>> ')
                counter += 1
                continue

            while counter <= 5 and (len(password) < 4 or password.find(' ') > -1 ):
                print('password must be at least 4 characters, no spaces')
                password = getpass('password:\n>> ')
                counter += 1
                continue
            
            while password != password2:
                password2 = getpass('repeat password:\n>> ')
                if password != password2:
                    print('passwords don\'t match')

            util.send_message(self.socket, f'{username} {password}', self.chunk_size)
            
            instructions = util.get_instructions(self.socket, self.chunk_size)
            
            if instructions == 'welcome':
                return True
            else: 
                counter += 1

        if counter > 5:
            print('error getting credentials for new account')
            return False

    def _receive_list(self):
        #data = b''
        chunk = util.get_instructions(self.socket, self.chunk_size)
        print('---------------')
        while chunk.find((util.stop_phrase).decode('utf-8')) == -1:
            logger.debug(f'in list: received {chunk}')
            print(f'{chunk}')
            chunk = util.get_instructions(self.socket, self.chunk_size)
        print('---------------')
        return True


    def client_protocol(self):
        filename = ''
        logged_in = False
        print('login or create an account using acc')
        while True:

            if not logged_in:
                data = input(">> ")
            else:
                print('list, upload, download, delete, or logout')
                data = input("u>> ")

            if len(data) < 1:
                continue
            else:
                commands = data.split()
                command = commands[0]
                if len(commands) > 1:
                    filename = commands[1]
                    util.send_message(self.socket, f'{command} {filename}', self.chunk_size)
                else:
                    util.send_message(self.socket, f'{command}', self.chunk_size)
            
            if command.find( CLOSE) > -1:
                logged_in = False
                self.socket.close()
                break

            if command.find(LOGOUT) > -1:
                logged_in = False
                continue
                
            if not logged_in:
                if command == LOGIN:
                    logged_in = self._login()
                elif command == ACC:
                    logged_in = self.create_account()
                else:
                    logger.error(f'wrong command {command}')
                    print(f'wrong command {command} try login or acc')
            else:
                file_path = f'{self.dir_path}/{filename}'
                if command == LIST:
                    self._receive_list()
                
                if filename == '':
                    print(f"to use {command} provide a file name")
                    continue

                if command ==  DOWNLOAD:
                    util.receive_file(self.socket, self.dir_path + '/' + filename, self.chunk_size, True)

                elif command == UPLOAD: 
                    if os.path.exists(file_path):
                            print(f'start upload of file {filename} from {file_path}')
                            util.send_file(self.socket, self.dir_path +'/' + filename, self.chunk_size)
                    else:
                        print(f'no file {filename} found to upload')

                elif command == DELETE:
                    continue

            continue

        


def main():

    if len(sys.argv) > 1:
        middleware_port = int(sys.argv[1])
    else:
        logger.error(f"no port identified for client")

    if len(sys.argv) > 2:
        chunk_size = int(sys.argv[2])
    else:
        logger.info(f"defaulting to chunk size 32")


    client_socket = socket.socket()
    host = socket.gethostname()
    try:
        client_socket.connect((host, middleware_port))
        logger.info(f'bound successfully to {middleware_port}')

    except socket.error as msg: 
        logger.info("Socket binding error: " + str(msg) + "\n" + "Retrying...")
    
    local_client = Client(client_socket)
    local_client.client_protocol()


if __name__ == "__main__":
    main()