
import argparse
import os
import sys

import socket
import logging

DEBUG = True
chunk_size = 64
stop_phrase = b"<><><><<<<<>>><>>>"
fh = logging.FileHandler('logfile.log')
logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.server')
logger.addHandler(fh)
if not DEBUG:
    logging.disable(logging.DEBUG)


def cut_chunks(lst):
    return [lst[i * chunk_size : (i + 1) * chunk_size] for i in range((len(lst) + chunk_size - 1) // chunk_size)]


def create_chunks(lst):
    n = chunk_size
    return [lst[i * n:(i + 1) * n].encode('utf-8') for i in range((len(lst) + n - 1) // n )]


def end_seq(num: int):
    return ('x' + str(num)).encode('utf-8')


def get_pad_chunks(zero_pad_chunks_count: int, chunk_size: int, end_seq):
    chunks = []
    
    while zero_pad_chunks_count != 0:
        chunk = b'0' * chunk_size
        chunks.append(chunk)
        zero_pad_chunks_count -= 1
    
    chunk = b'0' * (chunk_size - len(end_seq)) + end_seq
    print(type(chunk))
    chunks.append(chunk)
    return chunks


def process_chunks(data: bytes, chunk_size: int):
    '''
        + checks if the last chunk needs to be padded
        + pads the last quad of chunks, adding full zero chunks
        + adds info about padding to the end of the file
        + ALWAYS pads, so middleware ALWAYS must cut off padding before sending data to client
    '''
    chunks = cut_chunks(data)
    logger.debug(f'\nchunks: {chunks}')
    zero_pad = 0
    zero_chunks_to_pad = 0
    if len(chunks) % 4 != 0:
        zero_chunks_to_pad += (len(chunks) % 4)
    
    zero_pad = 0
    
    if len(chunks[-1]) < chunk_size:
        zero_pad += (chunk_size - len(chunks[-1]))

    total_padding = zero_pad + zero_chunks_to_pad*chunk_size

    if total_padding < 2:
        total_padding += chunk_size * 4
        zero_chunks_to_pad += 4

    end_sequence = end_seq(total_padding)
    logger.debug(f'end sequece: {end_sequence}')
    if total_padding < chunk_size:
        # adjusts to possible needed length of end sequence
        if total_padding > len(str(chunk_size)): 
            chunks[-1] += (b'0' * (zero_pad - len(end_sequence)) + end_sequence)

    else:
        chunks[-1] += (b'0' * zero_pad)
        logger.debug(f'get pad chunks')
        pad_chunks = get_pad_chunks(zero_chunks_to_pad, chunk_size, end_sequence)
        logger.debug(f'pad chunks: {pad_chunks}')
        for chunk in pad_chunks:
            chunks.append(chunk)
    
    return chunks



def get_chunks(file_name: str):
    
    with open(file_name, 'rb') as f:
        chunks = []
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                chunks.append(chunk)

def xor(b1, b2):
    return bytes(x ^ y for x, y in zip(b1, b2))

def assembleAB(nodes:list, file_a:str, file_b:str):
    logger.debug(f"Assembling:\nFile a: {file_a} ({type(file_a)}\nFile b: {file_b} ({type(file_b)})")
    with open(file_a, 'rb') as fa, open(file_b, "rb") as fb, open(file_a[:-1], 'wb') as target:
         chunkA1 = fa.read(chunk_size)
         chunkA2 = fb.read(chunk_size)
         chunkB1 = fa.read(chunk_size)
         chunkB2 = fb.read(chunk_size)
         while chunkA1:
            target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)
            chunkA1 = fa.read(chunk_size)
            chunkA2 = fb.read(chunk_size)
            chunkB1 = fa.read(chunk_size)
            chunkB2 = fb.read(chunk_size)


def assembleAC(nodes: list, file_a: str, file_c: str):
    with open(file_a, 'rb') as fa, open(file_c, "rb") as fc, open(file_a[:-1], 'wb') as target:
        chunkA1 = fa.read(chunk_size)
        chunkB1 = fa.read(chunk_size)
        chunkC1 = fc.read(chunk_size)
        chunkC2 = fc.read(chunk_size)

        chunkA2 = xor(chunkC1, chunkA1)
        chunkB2 = xor(chunkC2, chunkB1)
        while True:
            target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)
            chunkA1 = fa.read(chunk_size)
            chunkB1 = fa.read(chunk_size)
            chunkC1 = fc.read(chunk_size)
            chunkC2 = fc.read(chunk_size)

            chunkA2 = xor(chunkC1, chunkA1)
            chunkB2 = xor(chunkC2, chunkB1)

def assembleAD(nodes: list, file_a: str, file_d: str):
    with open(file_a, 'rb') as fa, open(file_d, "rb") as fd, open(file_a[:-1], 'wb') as target:
        chunkA1 = fa.read(chunk_size)
        chunkB1 = fa.read(chunk_size)
        chunkD1 = fd.read(chunk_size)
        chunkD2 = fd.read(chunk_size)

        chunkA2 = xor(chunkD1, chunkB1)
        chunkB2 = xor(chunkB1, xor(chunkD2, chunkA1))

        while True:
            target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)
            chunkA1 = fa.read(chunk_size)
            chunkB1 = fa.read(chunk_size)
            chunkD1 = fd.read(chunk_size)
            chunkD2 = fd.read(chunk_size)

            chunkA2 = xor(chunkD1, chunkB1)
            chunkB2 = xor(chunkB1, xor(chunkD2, chunkA1))

def assembleBC(nodes: list, file_b: str, file_c: str):
    with open(file_b, 'rb') as fb, open(file_c, "rb") as fc, open(file_b[:-1], 'wb') as target:
        chunkA2 = fb.read(chunk_size)
        chunkB2 = fb.read(chunk_size)
        chunkC1 = fc.read(chunk_size)
        chunkC2 = fc.read(chunk_size)

        chunkB1 = xor(chunkC2, chunkB2)
        chunkA1 = xor(chunkC1, chunkA2)
        
        while True:
            target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)
            chunkA2 = fb.read(chunk_size)
            chunkB2 = fb.read(chunk_size)
            chunkC1 = fc.read(chunk_size)
            chunkC2 = fc.read(chunk_size)

            chunkB1 = xor(chunkC2, chunkB2)
            chunkA1 = xor(chunkC1, chunkA2)

def assembleBD(nodes: list, file_b: str, file_d: str):
    with open(file_b, 'rb') as fb, open(file_d, "rb") as fd, open(file_b[:-1], 'wb') as target:
        chunkA2 = fb.read(chunk_size)
        chunkB2 = fb.read(chunk_size)
        chunkD1 = fd.read(chunk_size)
        chunkD2 = fd.read(chunk_size)

        
        chunkB1 = xor(chunkD1, chunkA2)
        chunkA1 = xor(chunkB1, xor(chunkD2, chunkB2))

        while True:
            target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)
            chunkA2 = fb.read(chunk_size)
            chunkB2 = fb.read(chunk_size)
            chunkD1 = fd.read(chunk_size)
            chunkD2 = fd.read(chunk_size)

        
            chunkB1 = xor(chunkD1, chunkA2)
            chunkA1 = xor(chunkB1, xor(chunkD2, chunkB2))



def assembleCD(nodes: list, file_c: str, file_d: str):
    with open(file_c, 'rb') as fc, open(file_d, "rb") as fd, open(file_c[:-1], 'wb') as target:
        chunkC1 = fc.read(chunk_size)
        chunkC2 = fc.read(chunk_size)
        chunkD1 = fd.read(chunk_size)
        chunkD2 = fd.read(chunk_size)

        chunkA1 = xor(chunkD2, chunkC2)
        chunkA2 = xor(chunkC1, chunkA1)
        chunkB1 = xor(chunkD1, chunkA2)
        chunkB2 = xor(chunkC2, chunkB1)

        while True:
            target.write(chunkA1 + chunkA2 + chunkB1 + chunkB2)
            chunkC1 = fc.read(chunk_size)
            chunkC2 = fc.read(chunk_size)
            chunkD1 = fd.read(chunk_size)
            chunkD2 = fd.read(chunk_size)

            chunkA1 = xor(chunkD2, chunkC2)
            chunkA2 = xor(chunkC1, chunkA1)
            chunkB1 = xor(chunkD1, chunkA2)
            chunkB2 = xor(chunkC2, chunkB1)




def pad_message(message:str):
    
    data = str(message).encode('utf-8')
    
    zeroes_to_pad = chunk_size - len(data)
    data += b'0' * zeroes_to_pad 
    zeroes_count = str(zeroes_to_pad).encode('utf-8')
    
    data += b'0' * (chunk_size - len(zeroes_count)) + zeroes_count

    #logger.debug(f'zeroes to pad = {zeroes_to_pad}')
    logger.debug(f'data: {data[:20]}... len: {len(data)}')

    return data


def get_instructions(csoc: socket.socket, chunk_size: int, auto_print: bool = True, auto_decode: bool = True):
    '''
    
    '''
    #logger.debug("Get instructions:")
    data = csoc.recv(2*chunk_size)
    if len(data) == 0:
        return ''
    instruction = data.decode("utf-8")
    #logger.debug(f'instruction = {instruction}')
    try:
        pad_count = int(instruction[chunk_size:])
    except ValueError:
        return ''
    #logger.debug(f'pad count = {pad_count} ')
    instruction = instruction[:(chunk_size - pad_count)]
    if auto_print:
        print(f"instruction<= {instruction}")
    if auto_decode:
        return instruction
    else:
        return instruction.encode('utf-8')
    

def send_message(csoc: socket.socket, message:str, chunk_size:int):
    if message == '':
        return
    if not message:
        return
    data = pad_message(message)
    #print(f'{data[:10]}')
    csoc.sendall(data)


def receive_file(csoc: socket.socket, file_name: str, chunk_size: int, final_client_file_is_to_be_received=False):
    previous_chunk = b''
    data = b''
    num_chunks = 0
    f = open(file_name, "wb")
    logger.info('file opened. receiving data...')
        
    while True:
        data = csoc.recv(chunk_size)
        if not data or data == '':
            break
        stop_phrase_index = data.find(stop_phrase)
        # check for stop phrase
        num_chunks += 1
        logger.debug(f"Received: {data}")
        if stop_phrase_index != -1:
            nullbyte_count = int(data[:stop_phrase_index].decode("UTF-8"))
            # Would not work correctly if it == 0 so we need this check
            if nullbyte_count > 0: 
                # cut off padding
                previous_chunk = previous_chunk[:-nullbyte_count]
            # Dumb hot fix for dumb code
            if final_client_file_is_to_be_received:
                try:
                    dumb_nullbyte_split_char = b"x"
                    dumb_nullbyte_split_char_index = previous_chunk.rfind(dumb_nullbyte_split_char)
                    dumb_nullbyte_count_as_str = previous_chunk[dumb_nullbyte_split_char_index + 1:]
                    end_seq_length = int(dumb_nullbyte_count_as_str)
                    previous_chunk = previous_chunk[:len(previous_chunk) - end_seq_length]
                except:
                    logger.debug("Nu huevo, cho")
            f.write(previous_chunk)
            break
            
        else:
            f.write(previous_chunk)
            num_chunks += 1
            previous_chunk = data

    f.close()
    logger.info('Successfully got the file')
    return num_chunks


def send_file(csoc: socket.socket, file_name: str, chunk_size: int):
    counter = 0
    logger.debug(f'Sending file {file_name}')
    try:    
        with open(file_name, 'rb') as f:
            chunk = f.read(chunk_size)
            nullbyte_count = 0
            while chunk:
                
                nullbyte_count = chunk_size - len(chunk)
                if nullbyte_count != 0:
                    chunk += b'0' * nullbyte_count
                csoc.send(chunk)
                counter += 1
                if counter % 10:
                    logger.info(f'Sent {chunk}')
                chunk = f.read(chunk_size)
            
            final_chunk = (("0" if nullbyte_count < 10 else "") + f"{nullbyte_count}{stop_phrase.decode('utf-8')}").encode('utf-8')
            
            csoc.send(final_chunk)
        logger.info("file closed")
    except FileNotFoundError:
        send_message(csoc, stop_phrase.decode('utf-8'), chunk_size)
        print('file not found')

def is_accessible(file_name):
    try:
        f = open(file_name)
        f.close()
    except IOError:
        return False
    return True
