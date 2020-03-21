import socket
import argparse
import os
import logging

import sys
from pathlib import Path

from util import send_file, receive_file, is_accessible, stop_phrase

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
logger = logging.getLogger('data_storage.server')
logger.addHandler(fh)


class Node:
    is_connected: bool
    def __init__(self, host, port, dir_path):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.dir_path = dir_path
        #self.socket.bind((host, port))
    
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            is_connected = True;
        except:
            logger.error(f"{self.port} failed to connect in node")
            is_connected = False

def create_account(csoc, dir_path, username, password):
    dir_list = os.listdir(".")
    if not dir_list.find(f"{username}-{password}"):
        os.mkdir(f"{username}-{password}", mode=0o770)
        return f"{username}-{password}"
    else:
        return ""

def login(csoc, dir_path, username, password):
    dir_list = os.listdir(".")
    if dir_list.find(f"{username}-{password}"):
        return f"./{username}-{password}"
    else:
        return "./"

def list_acc(csoc, dir_path):
    dir_list = os.listdir(dir_path)
    dir_list = [i.encode("utf-8") for i in dir_list]
    for item in dir_list:
        csoc.sendall(b"- \t" + item + b"\n")
    csoc.sendall(stop_phrase)
    
def server_protocol(csoc, dir_path):
#    dir_path = Path.cwd(
    logged_in = -1
    while True:
        data = csoc.recv(chunk_size)
        logger.info(data)
        command, name = (data.decode("utf-8")).split()
        logger.info(f"received {command} and {name}")
        if command == CLOSE:
            csoc.close()
            break
        elif logged_in == 1:
            if command == DELETE and is_accessible(name):
                try:
                    os.remove(name);
                    logger.info(f"{name} removed successfully")
                except:
                    logger.error(f"{name} was not removed")
            elif command == LIST:
                list_acc(csoc, dir_path)
            elif command == UPLOAD:
                receive_file(csoc, dir_path, name)
            elif command == DOWNLOAD and is_accessible(name):
                send_file(csoc, dir_path, name)
            elif command == LOGOUT:
                dir_path = "./"
                logged_in = -1
            else:
                csoc.sendall(b'invalid command' + command)
        else:
            if command == LOGIN:
                dir_path = login(csoc, name)
                if (dir_path != "./"):
                    csoc.sendall("welcome".encode("utf-8"))
                    logged_in = 1
                else:
                    csoc.sendall("wrong username or password")
                    continue
            elif command == ACC:
                dir_path += create_account(csoc, name)
                if dir_path != "./":
                    csoc.sendall("account created".encode("utf-8"))
                else:
                    csoc.sendall("account already exists".encode("utf-8"))
            
            else: 
                csoc.sendall(b'invalid command')
                continue 



def main():

    if len(sys.argv) > 1:
        dir_path = Path.cwd() + '/' + str(sys.argv[1])
    else:
        raise ValueError("STORAGE NODE NOT IDENTIFIED")

    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        raise ValueError(f"PORT FOR NODE {sys.argv[1]} IS NOT IDENTIFIED")

    if len(sys.argv) > 3:
        chunk_size = int(sys.argv[3])
    else:
        logger.info("defaulting to chunk size {chunk_size}")

    s = socket.socket()             # Create a socket object
    host = socket.gethostname()     # Get local machine name
    s.bind((host, port))            # Bind to the port
    s.listen(5)                     # Now wait for client connection.

    print  ('Server listening....')

    while True:
        conn, addr = s.accept()     # Establish connection with client.
        print('Got connection from', addr)
        # data = conn.recv(chunk_size)
        # print('Connection received', repr(data))

        server_protocol(conn, dir_path)

        conn.send('Thank you for connecting')
        conn.close()

if __name__ == "__main__":
    main()