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





def create_account(csoc: socket.socket, dir_path: str, name: str):
    
    dir_list = os.listdir(dir_path)
    
    try:
        dir_list.index(f"{name}")
        return 2, ""

    except ValueError:
        os.mkdir(dir_path+f"/{name}")
        print(f'created a folder at {dir_path}')
        return 1, f"{name}"


def login(csoc: socket.socket, dir_path: str, name: str):
    dir_list = os.listdir(dir_path)
    try:
        dir_list.index(name)
        return 1, f"{dir_path}/{name}"
    except ValueError:
        return 2, dir_path
        


def list_acc(csoc: socket.socket, dir_path: str):
    dir_list = os.listdir(dir_path)
    stringy_dir_list = '\n'.join(dir_list)

    logger.info(f'{stringy_dir_list}')
    dir_list = util.cut_chunks(stringy_dir_list)

    for item in dir_list:
        util.send_message(csoc, item, chunk_size)
        util.send_message(csoc, item, chunk_size)
    logger.info('sent all directory')
    util.send_message(csoc, (util.stop_phrase).decode('utf-8'), chunk_size)


def server_protocol(csoc, dir_path, identity):
#    dir_path = Path.cwd(
    curr_path = dir_path
    logged_in = False
    first_time = True
    while True:
        if first_time:
            print('waiting for instructions...')
        
        data = util.get_instructions(csoc, chunk_size)

        if (len(data) == 0) and first_time:
            if first_time:
                logger.error(f'in {curr_path}:: data: {data} type {type(data)} len {len(data)}')
            first_time = False
            continue

        first_time = True

        if data.find(' ') > -1:
            command, name = str(data).split()
            logger.debug(f"in {curr_path}:: received {command} and {name}")
        else:
            command = str(data)
            logger.debug(f'in {curr_path}:: received {command} type of command {type(command)}')

        if command == ID:
            util.send_message(csoc, identity, chunk_size)
            continue
        elif command == CLOSE:
            return True

        elif command == LOGOUT:
            logged_in = False
            curr_path = dir_path
            continue

        if logged_in == False:
            if command == LOGIN:
                result, curr_path = login(csoc, dir_path, name)

                if (curr_path != dir_path):
                    
                    util.send_message(csoc, result, chunk_size)
                    logged_in = True
                    continue
                else:
                    util.send_message(csoc, result, chunk_size)
                    continue

            elif command == ACC:
                
                result, curr_path = create_account(csoc, dir_path, name)
                if curr_path != dir_path:
                    # account creation is successful
                    util.send_message(csoc, '1', chunk_size) 
                    
                else:
                    # account creation is not successful
                    util.send_message(csoc, '2', chunk_size)
            else: 
                # command is unknown
                util.send_message(csoc, '-1', chunk_size)
                continue 

        elif logged_in == True:
            if command == DELETE:
                try:
                    os.remove(f'{curr_path}/{name}')
                    logger.info(f"{curr_path}/{name}' removed successfully")
                    
                except FileNotFoundError:
                    logger.error(f"{curr_path}/{name}' DNE")
                    
            elif command == LIST:
                logger.debug(f'got to {command}')
                list_acc(csoc, curr_path)

            elif command == UPLOAD:
                util.receive_file(csoc, f'{curr_path}/{name}', chunk_size)

            elif command == DOWNLOAD:
                util.send_file(csoc, f'{curr_path}/{name}', chunk_size)

            else:
                logger.info(f'{csoc} invalid command {command}, {chunk_size}')

def main():
    chunk_size = 64
    logger.info(f'\nsys.argv = {sys.argv}\n')
    if len(sys.argv) > 1:
        identity = sys.argv[1]
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

            result = server_protocol(conn, dir_path, identity)
    conn.close()



if __name__ == "__main__":
    main()