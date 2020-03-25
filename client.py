import socket
import argparse
import os
import logging

import sys
from pathlib import Path

from getpass import getpass

from util import send_file, receive_file, is_accessible, send_message, get_instructions

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

port =  6000
chunk_size = 32

fh = logging.FileHandler('logfile.log')
logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.client')
logger.addHandler(fh)


class Client:
    is_connected: bool
    logged_in: bool
    
    def __init__(self, connection_name:str, host: int, port:int, dir_path:str, chunk_size:int):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.dir_path = dir_path
        self.connection_name = connection_name
        self.chunk_size = chunk_size
    
    def connect(self):
        try:
            self.socket.bind((self.host, self.port))
            logger.info(f"client connected to {port}")
            is_connected = True;
            logged_in = False
        except:
            logger.error(f"{self.port} failed to bind to client")
            is_connected = False

    def _login(self):
        instructions = get_instructions(self.socket, self.chunk_size)
        username = input('>> ')
        send_message(self.socket, username)
        instructions = get_instructions(self.socket, self.chunk_size)
        password = getpass('>> ')
        send_message(self.socket, password)
        instructions = get_instructions(self.socket, self.chunk_size)
        if instructions == 'welcome':
            return True
        else: 
            return False

    def create_account(self):
        instructions = get_instructions(self.socket, self.chunk_size)
        username = input('>> ')
        send_message(self.socket, username)

        instructions = get_instructions(self.socket, self.chunk_size)
        password = getpass('>> ')
        send_message(self.socket, password)

        instructions = get_instructions(self.socket, self.chunk_size)
        password = getpass('repeat password:\n>> ')
        send_message(self.socket, password)
        instructions = get_instructions(self.socket, self.chunk_size)
        if instructions == 'welcome':
            return True
        else: 
            return False

    def _receive_list(self):
        data = b''
        chunk = b''
        while chunk.find(stop_phrase) == -1:
            print(chunk)
            chunk = get_instructions(self.socket, self.chunk_size)

    def client_protocol(self):
        instructions = get_instructions(self.socket, self.chunk_size)
        instructions = get_instructions(self.socket, self.chunk_size)
        while True:

            commands = input(">> ").split()
            command = commands[0]
            if len(command) > 1:
                filename = " " + commands[1]
            else:
                filename = ""
            send_message(self.socket, command + filename)
    
            if command == CLOSE:
                self.logged_in = False
                self.socket.close()
            if not self.logged_in:
                if command == LOGIN:
                    self.logged_in = self._login()
                elif command == ACC:
                    self.logged_in = self.create_account()
                else:
                    logger.error(f'wrong command {command}')
                    print(f'wrong command {command} try login or acc')
            else:
                if command == LIST:
                    self._receive_list()
                if command ==  DOWNLOAD or command == UPLOAD or command == DELETE:
                    if not filename:
                        print(f"to use {command} provide a file name")
                    else:
                        instructions = self.receive_instructions()
                        if command == DOWNLOAD:
                            receive_file(self.socket, self.dir_path +'/' + filename, self.chunk_size)
                        elif command == UPLOAD:
                            send_file(self.socket, self.dir_path +'/' + filename, self.chunk_size)
                        elif command == DELETE:
                            if not get_instruction(self.socket, self.chunk_size) == f'{filename} was deleted successfully':
                                logger.error(f'error deleting file {filename}')
                            else:
                                logger.info(f'file {filename} deleted successfully')
                if command == LOGOUT:
                    self.logged_in = False
                
            continue

        


def main():

    if len(sys.argv) > 1:
        dir_path = str(Path.cwd()) + '/' + str(sys.argv[1])
    else:
        raise ValueError("STORAGE NODE NOT IDENTIFIED")

    if len(sys.argv) > 2:
        middleware_port = int(sys.argv[2])
    else:
        raise ValueError(f"PORT FOR NODE {sys.argv[1]} IS NOT IDENTIFIED")

    if len(sys.argv) > 3:
        self.chunk_size = int(sys.argv[3])
    else:
        logger.info("defaulting to chunk size {self.chunk_size}")


    client_socket = socket.socket()
    try:
        client_socket.connect(("middleware", middleware_port))
    except:
        logger.error(f"failed to bind to {middleware_port}. check port value")
    
    client_protocol(client_socket)

    client_protocol.close()


if __name__ == "__main__":
    main()