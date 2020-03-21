import socket
import argparse
import os
import logging

import sys

stop_phrase = b"<><><><<<<<>>><>>>"
fh = logging.FileHandler('logfile.log')
logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.server')
logger.addHandler(fh)



def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

def send_message(csoc: socket.socket, data: str):
    message = bytearray(data, 'utf-8')
    csoc.sendall(message)


def receive_file(csoc: socket.socket, file_name: str, chunk_size: int):
    previous_chunk = b''
    data = b''
    
    f = open(file_name, "wb")
    logger.info('file opened')
        
    while True:
        logger.info('receiving data...')
        data = csoc.recv(chunk_size)
        logger.info(f'Received {len(data)} {data.decode("UTF-8")}')
    
        stop_phrase_index = data.find(stop_phrase)
        # check for stop phrase
        if stop_phrase_index != -1:
            nullbyte_count = int(data[:stop_phrase_index].decode("UTF-8"))
                # Would not work correctly if it == 0 so we need this check
            if nullbyte_count > 0: 
                # cut off padding
                previous_chunk = previous_chunk[:-nullbyte_count]
                f.write(previous_chunk)
                break
            
        else:
            f.write(previous_chunk)
            previous_chunk = data

    f.close()
    logger.info('Successfully got the file')


def get_instructions(csoc: socket.socket, chunk_size: int, auto_print: bool = True, auto_decode: bool = True):
    data = csoc.recv(chunk_size)
    instruction = data.decode("utf-8")
    if auto_print:
        print(instruction)
    if auto_decode:
        return instruction
    else:
        return data


def send_file(csoc, file_name, chunk_size):
    with open(file_name,'rb') as f:
        chunk = f.read(chunk_size)
        nullbyte_count = 0
        while chunk:
            nullbyte_count = chunk_size - len(chunk)
            if nullbyte_count != 0:
                chunk += b'0' * nullbyte_count
            csoc.send(chunk)
            logger.info('Sent ', repr(chunk))
            chunk = f.read(chunk_size)
        final_chunk = ("0" if nullbyte_count < 10 else "") + f"{nullbyte_count}{stop_phrase.decode('utf-8')}"
        final_chunk = final_chunk.encode('utf-8')
        csoc.send(final_chunk)
    logger.info("file closed")

def is_accessible(file_name):
    try:
        f = open(file_name)
        f.close()
    except IOError:
        return False
    return True
