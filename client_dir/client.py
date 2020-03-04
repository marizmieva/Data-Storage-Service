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


def receive_file(csoc, file_name):
    with open(file_name, 'wb') as f:
        print ('file opened')
        while True:
            logger.info('receiving data...')
            data = csoc.recv(chunk_size)
            logger.info('Received {} {}'.format(len(data), data))
            if not data:
                break
            f.write(data)
            if len(data) < chunk_size:
                break
    logger.info('Successfully got the file')


def send_file(csoc, file_name):
    f = open(file_name,'rb')
    chunk = f.read(chunk_size)
    while chunk:
       csoc.send(chunk)
       logger.info('Sent ',repr(chunk))
       chunk = f.read(chunk_size)
    csoc.send(b'')
    f.close()
    logger.info("file closed")


def client_protocol(csoc):
    while True:
        command, file_name = (input(">> ")).split()
        if command == CLOSE:
            csoc.sendall((command).encode("utf-8"))
            print("commands sent")
            csoc.close()
            print('connection closed')
            return 
        elif command == DOWNLOAD:
            csoc.sendall((command + " " + file_name).encode("utf-8"))
            logger.info("commands sent")
            receive_file(csoc, file_name)
        elif command == UPLOAD:
            csoc.sendall((command + " " + file_name).encode("utf-8"))
            logger.info("commands sent")
            send_file(csoc, file_name)
        elif command == DELETE:
            csoc.sendall((command + " " + file_name).encode("utf-8"))
        else:
            print(f"Invalid command {file_name}")


def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    if len(sys.argv) > 2:
        chunk_size = sys.argv[2]

    s = socket.socket()    
    host = socket.gethostname()     

    s.connect((host, port))
    #s.send("Hello server!".encode("utf-8"))

    client_protocol(s)
    s.close()


if __name__ == "__main__":
    main()