import socket
import argparse
import os
import logging

import sys
from pathlib import Path


logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.server')


DOWNLOAD = "download"
UPLOAD = "upload"
CLOSE = "close"
DELETE = "delete"

port =  6000
chunk_size = 32


def is_accessible(file_name):
    try:
        f = open(file_name)
        f.close()
    except IOError:
        return False
    return True


def send_message(csoc, str):
    message = bytearray(str, 'utf-8')
    csoc.sendall(message)


def receive_file(csoc, file_name):
    with open(file_name, 'wb') as f:
        logger.info('file opened')
        while True:
            logger.info('receiving data...')
            data = csoc.recv(chunk_size)
            logger.info('Received {} {}'.format(len(data), data))
            if not data:
                break
            f.write(data)
            if len(data) < chunk_size:
                break
    f.close()
    logger.info('Successfully got the file')


def send_file(csoc, file_name):
    with open(file_name,'rb') as f:
        chunk = f.read(chunk_size)
        csoc.send(chunk)
        logger.info(f'sent {chunk}')
        #f.close()
    logger.info("file closed")
    send_message(csoc, "\0" * chunk_size * 10)

def server_protocol(csoc):
    while True:
        data = csoc.recv(chunk_size)
        logger.info(data)
        command, file_name = (data.decode("utf-8")).split()
        logger.info(f"received {command} and {file_name}")
        if command == DELETE and is_accessible(file_name):
            try:
                os.remove(file_name);
                logger.info(f"{file_name} removed successfully")
            except:
                logger.error(f"{file_name} was not removed")
        elif command == UPLOAD:
            receive_file(csoc, file_name)
        elif command == DOWNLOAD and is_accessible(file_name):
                send_file(csoc, file_name)
        elif command == CLOSE:
            csoc.close()
            logger.info('connection closed')
            return        
        else: 
            csoc.sendall(b'invalid command')
            continue 



def main():

    if len(sys.argv) > 1:
        port = sys.argv[1]
    if len(sys.argv) > 2:
        chunk_size = sys.argv[2]

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

        server_protocol(conn)

        conn.send('Thank you for connecting')
        conn.close()

if __name__ == "__main__":
    main()