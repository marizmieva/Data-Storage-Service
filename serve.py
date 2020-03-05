import socket
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('data_storage')
logger = logging.getLogger('data_storage.server')

# 1) Make Server class that will be both for sender and reciever and interactive/non-interactive functions (BUT WITH DIFFERENT FUCKING NAMES WTF INTERACTIVE NON INTERACTIVE BLYAT)
# 2) Make AbstractBaseClass Server and inherit both reciever and sender from it, and implement the abstract "HandleTransaction" (or anything else) method in there for each.

DOWNLOAD = "download"
UPLOAD = "upload"
CLOSE = "close"

def file_is_accessible (file_name):
    try:
        f = open(file_name)
        f.close()
    except IOError:
        logger.info(f"{file_name} is not available")
        return False
    logger.info(f"{file_name} is available")   
    return True


class Data_Node:
    standard_commands = ["download", "upload", "close"]
    def __init__(self, csoc, chunk_size, interactive=0):
        
        self.csoc = csoc
        self.chunk_size = chunk_size
        self.interactive= interactive

    def send_message(self, message):
        self.csoc.sendall(message.encode("utf-8"))

    def receive_file(self, file_name):
        # No error handling
        with open(file_name, 'wb') as f:
            print ('file opened') # replace with logging
            while True:
                print('receiving data...') # replace with logging
                data = self.csoc.recv(chunk_size)
                logger.info('Received {} {}'.format(len(data), data))
                if not data: # What if data is empty on the first iteration?
                    break
                f.write(data)
                if len(data) < self.chunk_size:
                    break
        f.close() # Delete. 'with' closes the file automatically
        logger.info('Successfully got the file')

    def send_file(self, file_name):
        f = open(file_name,'rb') # replace with 'with' statement
        chunk = f.read(self.chunk_size)
        while chunk:
            self.csoc.send(chunk)
            logger.info('Sent ', repr(chunk))
            chunk = f.read(self.chunk_size)
        logger.info("file successfully sent")
        f.close() # replace with 'with' statement
        logger.info("file closed") # Not necessary with 'with' statement as it will close the file no matter what
        #self.csoc.send(stop.encode("utf-8")) # Almost the same as send_message(self, message)

    def handle_request(self):
        while True:
            # Receive command
            data = self.csoc.recv(self.chunk_size)
            command, file_name = (data.decode("utf-8")).split()
            logger.info(f"received command {command} for  {file_name} ")
            # Handle command
            if command == UPLOAD:
                receive_file(self.csoc, file_name) 
            elif command == DOWNLOAD:
                send_file(self.csoc, file_name)
            elif command == CLOSE:
                self.csoc.close()
                logger.info('connection closed')
                return
            else:
                logger.warning("invalid command", command)
                self.csoc.sendall(b'invalid command')
                continue

    def make_request(self):
        while True:
            command, file_name = (input(">> ")).split()
            if command == DOWNLOAD:
                self.csoc.sendall((DOWNLOAD + " " + file_name).encode("utf-8"))
                receive_file(self.csoc, file_name)
            elif command == UPLOAD:
                self.csoc.sendall((UPLOAD + " " + file_name).encode("utf-8"))
                send_file(self.csoc, file_name)
            elif command == CLOSE:
                self.csoc.sendall((command).encode("utf-8"))
                self.csoc.close()
                logger.info("connection closed")
                return
            else:
                logger.warning("invalid command ", command)

    def run(self):
        if self.interactive == 1:
            self.interactive()
        else:
            self.not_interactive()


# def exists(path) -> bool:
#     return Path(path).exists()
# # Can move to util module if necessary

def main():
    pass

if __name__ == "__main__":
    main()