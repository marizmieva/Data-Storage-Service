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

def create_chunks(lst, n):
    
    return [lst[i * n:(i + 1) * n].encode('utf-8') for i in range((len(lst) + n - 1) // n )]


def end_seq(num):
    return ('x' + str(num)).encode('utf-8')


def get_pad_chunks(num, chunk_size, end_seq):
    chunks = []
    
    while num > 1:
        chunk = b'0' * chunk_size
        chunks.append(chunk)
    
    chunk = b'0' * (chunk_size - len(end_seq)) + end_seq
    print(type(chunk))
    chunks.append(chunk)
    return chunks

def process_chunks(data, chunk_size, size):
    '''
        + checks if the last chunk needs to be padded
        + pads the last quad of chunks, adding full zero chunks
        + adds info about padding to the end of the file
        + ALWAYS pads, so middleware ALWAYS must cut off padding before sending data to client
    '''
    chunks = create_chunks(data, chunk_size)
    byte_chunks = []
    chunks_to_pad = 0
    zero_pad = 0
    if len(chunks) % 4 != 0:
        zero_chunks_to_pad = (len(chunks) % 4)
    
    if len(chunks[-1]) < chunk_size:
        zero_pad = chunk_size - len(chunks[-1])

    total_padding = zero_pad + zero_chunks_to_pad*chunk_size

    if total_padding < 2:
        total_adding += chunk_size * 4
        zero_chunks_to_pad += 4

    end_sequence = end_seq(total_padding)

    if total_padding < chunk_size:
        # adjusts to possible needed length of end sequence
        if total_padding > len(str(chunk_size)): 
            chunks[-1] += (b'0' * (zero_pad - len(end_sequence) + end_sequence))
    else:
        chunks[-1] += (b'0' * zero_pad)
        pad_chunks = get_pad_chunks(zero_chunks_to_pad, chunk_size, end_sequence)
        for chunk in pad_chunks:
            chunks.append(chunk)
    
    return chunks



def get_chunks(file_name, chunk_size):
    
    with open(file_name, 'rb') as f:
        chunks = []
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                chunks.append(chunk)


def assembleAB(file_a, file_b, chunk_size):

    with open(file_a, 'rb') as fa, open(file_b, "rb") as fb, open(file_a[:-1], 'wb') as target:
         chunkA1 = fa.read(chunk_size)
         chunkA2 = fb.read(chunk_size)
         chunkB1 = fa.read(chunk_size)
         chunkB2 = fb.read(chunk_size)

         target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)



def assembleAC(file_a, file_c):
    with open(file_a, 'rb') as fa, open(file_c, "rb") as fc, open(file_a[:-1], 'wb') as target:
        chunkA1 = fa.read(chunk_size)
        chunkB1 = fa.read(chunk_size)
        chunkC1 = fc.read(chunk_size)
        chunkC2 = fc.read(chunk_size)

        chunkA2 = xor(chunkC1, chunkA1)
        chunkB2 = xor(chunkC2, chunkB1)

        target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)

def assembleAD(file_a, file_d):
    with open(file_a, 'rb') as fa, open(file_d, "rb") as fd, open(file_a[:-1], 'wb') as target:
        chunkA1 = fa.read(chunk_size)
        chunkB1 = fa.read(chunk_size)
        chunkD1 = fd.read(chunk_size)
        chunkD2 = fd.read(chunk_size)

        chunkA2 = xor(chunkD1, chunkB1)
        chunkB2 = xor(chunkB1, xor(chunkD2, chunkA1))

        target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)

def assembleBC(file_b, file_c):
    with open(file_b, 'rb') as fb, open(file_c, "rb") as fc, open(file_b[:-1], 'wb') as target:
        chunkA2 = fb.read(chunk_size)
        chunkB2 = fb.read(chunk_size)
        chunkC1 = fc.read(chunk_size)
        chunkC2 = fc.read(chunk_size)

        chunkA1 = xor(chunkC1, chunkB1)
        chunkB1 = xor(chunkC2, chunkB2)

        target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)

def assembleBD(file_b, file_d):
    with open(file_b, 'rb') as fb, open(file_d, "rb") as fd, open(file_b[:-1], 'wb') as target:
        chunkA2 = fb.read(chunk_size)
        chunkB2 = fb.read(chunk_size)
        chunkD1 = fd.read(chunk_size)
        chunkD2 = fd.read(chunk_size)

        
        chunkB1 = xor(chunkD1, chunkB1)

        chunkA1 = xor(chunkB1, xor(chunkD1, chunkB2))

        target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)


def assembleCD(file_c, file_d):
    with open(file_c, 'rb') as fc, open(file_d, "rb") as fd, open(file_c[:-1], 'wb') as target:
        chunkC1 = fc.read(chunk_size)
        chunkC2 = fc.read(chunk_size)
        chunkD1 = fd.read(chunk_size)
        chunkD2 = fd.read(chunk_size)

        chunkA1 = xor(chunkD2, chunkC2)
        chunkB1 = xor(chunkC1, chunkA1)
        chunkA2 = xor(chunkD1, chunkB1)
        chunkB2 = xor(chunkC2, chunkB1)

        chunkA1 = xor(chunkB1, xor(chunkD1, chunkB2))

        target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)


def xor(b1, b2):
    return bytes(x ^ y for x, y in zip(b1, b2))

def send_message(csoc: socket.socket, data: str):
    message = bytearray(data, 'utf-8')
    csoc.sendall(message)


def receive_file(csoc: socket.socket, file_name: str, chunk_size: int, target_file: str=""):
    previous_chunk = b''
    data = b''
    num_chunks = 0
    f = open(file_name, "wb")
    if target_file != "":
        t = open(target_file, 'wb')
    logger.info('file opened')
        
    while True:
        logger.info('receiving data...')
        data = csoc.recv(chunk_size)
        logger.info(f'Received {len(data)} {data.decode("UTF-8")}')
    
        stop_phrase_index = data.find(stop_phrase)
        # check for stop phrase
        num_chunks += 1
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
            num_chunks += 1
            previous_chunk = data

    f.close()
    logger.info('Successfully got the file')
    return num_chunks


def get_instructions(csoc: socket.socket, chunk_size: int, auto_print: bool = True, auto_decode: bool = True):
    '''
    hi
    '''
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
