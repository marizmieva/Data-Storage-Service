Client-Server Programming Online Storage System

1.	Project Description
The Online File Storage System accommodate central control and administration of files. It includes authentication procedure, an account creation procedure, as well as an upload, delete, download, and list functions. A redundant architecture of four data storage nodes instead of one, with data split between the four, should provide an ability to recover full data if two of the nodes are offline.
2.	Specifications
 
Figure 1. Structure
3.	Commands
Command	Description
acc	Create an account on the system
login	Log into the system
logout	Log out of system
list	List files currently stored in user’s directory
upload file name	Upload a file to the system
download file name	Download a file from the system
delete file name	Remove a file from the system

 

4.	Protocol
The Online File Storage protocol is a Request/Response half-duplex protocol. A client will send a request to the server, which will be followed by either an exchange of chunks of data or getting access to the files and information about them. The server receives, displays, updates and deletes files. Completion or failure to complete any operations is communicated back to the client. A client is limited to one request operation at a time. Once one request is sent, it will have to wait for a response before sending another request.
The protocol is a text-based protocol with a defined end-of-message indicator and mandatory padding.
Distribution Schemes
Middleware to Storage Nodes Distribution Scheme
1.	node A = chunk 0 xor chunk 2
2.	node B = chunk 1 xor chunk 3
3.	node C = ( chunk 0 xor chunk 1 + chunk 2 xor chunk 3)
4.	node D = (chunk 2 xor chunk 1 + chunk 0 xor (chunk 2 xor chunk 3)))
Middleware to Client File Assembly Scheme

1. AB <= nodeA[0] + nodeB[0] + nodeA[1] + nodeB[1]
 
2. AC <= nodeA[0] + xor(nodeC[0], nodeA[0]) + nodeB[1] + xor(nodeC[1], nodeA[1]) + 
 
3. AD <= nodeA[0] + xor(nodeD[0], nodeA[1]) + nodeA[1], xor(xor(nodeD[1], nodeA[0]), nodeA[1])
 
4. BC <= xor(nodeC[0], nodeB[0]) + nodeB[0] + xor(nodeC[1], nodeB[1]) + nodeB[1]
 
5. BD <= ii + i + iii + iv
    i   B[0] = xor(nodeD[0], nodeC[0])
    ii  A[0] = xor(nodeD[1], xor(nodeB[1], B[0]])
    iii A[1] = nodeB[0]
    iv  B[1] = nodeB[1]
 
6. CD <= xor(nodeD[1], nodeC[1]) + ii + iii + iv
    i   A[0] = xor(nodeD[1], nodeC[1])
    ii  A[1] = xor(nodeC[0], A[0])
    iii B[0] = xor(nodeD[0], A[1])
    iv  B[1] = xor(nodeC[1], B[0])

Padding schemes
Messaging Padding Scheme
Utilized functions: send_message, get_instructions
		Service functions: pad_message
When a chunk is sent through sockets, it gets padded with zeroes and an ‘x’ followed by the length of padding. Length of padding is everything from the end of original message and to the end of pre-defined chunk size. It is done by function send_message from util.py supplement, before it encodes and sends the chunk. When a message is received, a mirror function get_instructions finds the last x from the right of received and decoded, and cuts off the number of characters stated after it.
	File Padding Scheme
		Utilized functions: send_file, receive_file, to_servers, assemble_file, distribute_file
		Service functions: cut_chunks, create_chunks, end_sequence, test_assembly, assembleAB, assembleAC, assembleBC, assembleBD, assembleCD, xor
	When a file is sent from client to middleware, each sent and received chunk is not given padding, but if the last chunk is less than chunk size, then it gets padded, and the following chunk, called terminating chunk, includes a stop phrase (by design pre-configured in util.py as  b"<><><><<<<<>>><>>>") and zero padding with the same signaling set up as the messaging scheme, but it counts zeroes that were added to the previous chunk and well as padding of the terminating chunk itself.
Once middleware finds the stop phrase in the reception stream, follows the instructions in cutting off padding from the terminating chunk, throws it away, and writes the de-padded previous chunk to the file. Then, to send file to the storage nodes, it reads four times the length of the chunk from the file and passes it to the distributor function. That function cuts data into 4 chunks and distributes it according to scheme described above. Until the end of file is reached, and data can no longer be evenly divided into 4 chunks of pre-defined chunk size.
To pad data stored on storage nodes, length of data is compared to the pre-defined length of chunk. For example, if a chunk is supposed to be 8 bytes long, and the last section of the file ended up being only 3 bytes (b’EXA’), then the following operations will happen:
1.	Add enough zeroes to fill a whole chunk, store the number of zeroes
b’EXA00000’
2.	Then add zero chunks, and in the last chunk, store length of zero pad after an ‘x’, as such:

b’EXA0 0000’ b’0000 0000’ b’0000 0000’ b’0000 00x29’

After files are made even for the the above defined distribution scheme, it is implemented in the distribute file function, and the normal send_file function is not used by middleware->node connection, although the node still receives file using the receive file function, thus the terminating chunk is still used at the end of distribution.
When storage node sends the file to middleware, the node->middleware connection uses the normal send_file – receive file scheme. Middleware stores these files with the identity of the node at the end of its name and executes assemble file function.
Assemble file function reverses the distribution scheme, by reading 4 times the chunk length from files received from storage nodes (randomly chosen for the sake of simulating disconnected servers), and performing the operations described above. Once the file is reassembled, middleware sends it to the client, using the send_file->receive_file junction and standard file padding scheme.
Operations Implementations
Login 
		Utilized Functions: get_instructions, send_message, login, get_credentials, _login
		Service Functions: pad_message
1.	each account is a directory with username and password as directory name in plantext, a spectacularly safe solution
a	client asks user for username and password after sending login command to the middleware
b	middleware receives the command, followed by the username-password message, and sends it to the nodes
c	nodes check if such directory exists, and send 1 to middleware if it does or 2 if it does not
2.	if middleware got a 1 from all connected nodes, then it confirms login to the client, and client is then given a list of instructions that it can execute. if directory is not found, then user is asked to create a new such directory
3.	there exists no method of password recovery, so if password is lost then the directory is no longer accessible
Acc
Utilized Functions: get_instructions, send_message, create_account, generate_credentials
	Service Functions: pad_message

To create an account, user needs to send acc command to middleware. Then the following procedure is executed:
•	after sending acc command to the middleware, client is responsible for generation of proper username and password, according to the following rules:
a.	username must be at least 3 characters long
b.	password must be at least 4 characters long
c.	max size of username and password is limited by the chunk size
•	middleware receives the command, followed by the username-password message, and sends it to the nodes
•	nodes check if such directory exists, create it if it does not, and send 2 to middleware if it does or 1 if it does not
•	middleware communicates result to the client
Once the user is logged in the ‘>>’ which signifies that an instruction is expected get a ‘u’ at the end, and thus it starts looking as such: ‘u>>’.
Logout
Utilized Functions: get_instructions, send_message, logout
	Service Functions: pad_message
1.	input logout into client to move out of user’s directory, the instruction request drops the ‘u’ again
2.	middleware communicates the message to the nodes
3.	nodes leave user’s directory 
List
1.	input list to receive information about existing files in the data storage nodes in user’s directory
2.	have middleware request data storage nodes about files present at the directory
3.	if there are files, send their names will be send to the list, until a stop phrase is sent. Once it is sent, both client and middleware will stop receiving information
Upload filename
Utilized Functions: get_instructions, send_message, send_file, distribute_file
	Service Functions: pad_message, cut_chunks, create_chunks, end_sequence, xor

1.	input upload fileName to attempt to upload the file, which must be in your client directory, or else you will be notified of an error
2.	client sends file to the middleware, and middleware splits file according to the distribution scheme described in the above sections
3.	data nodes will override existing files if their names match the file user is sending
4.	respond to the client confirming successful upload, or otherwise respond with an error
Download filename
Utilized Functions: get_instructions, send_message, send_file, assmemble_file
	Service functions: cut_chunks, create_chunks, end_sequence, test_assembly, assembleAB, assembleAC, assembleBC, assembleBD, assembleCD, xor
1.	input download fileName in the client to attempt to download a file under that name
2.	have middleware send a request to data storage nodes to check if user’s directory
3.	if file does not exist, notify user about it
4.	otherwise, open file on data storage nodes as binary, and have middleware receive both, adding node’s identity to the end of the file names
5.	have middleware assemble the original file, according to the scheme described above, open a new file on client’s side, and receive data into it
6.	close files on both ends
7.	respond to the client confirming successful download, or otherwise respond with an error
Delete filename
Utilized Functions: get_instructions, send_message
Service functions: pad_message
1.	input delete fileName into client, to attempt to delete a file under provided file name
2.	middleware communicates message to the nodes
3.	server nodes try to remove the file using os.remove function
4.	result can be checked by using a list command
5.	Classes
CLASS MIDDLEWARE
Methods defined here:
__init__(self)
Initialize self.  See help(type(self)) for accurate signature.
assemble_data(self, client_connection, file_name)
1. AB <= nodeA[0] + nodeB[0] + nodeA[1] + nodeB[1]
 
2. AC <= nodeA[0] + xor(nodeC[0], nodeA[0]) + nodeB[1] + xor(nodeC[1], nodeA[1]) + 
 
3. AD <= nodeA[0] + xor(nodeD[0], nodeA[1]) + nodeA[1], xor(xor(nodeD[1], nodeA[0]), nodeA[1])
 
4. BC <= xor(nodeC[0], nodeB[0]) + nodeB[0] + xor(nodeC[1], nodeB[1]) + nodeB[1]
 
5. BD <= ii + i + iii + iv
    i   B[0] = xor(nodeD[0], nodeC[0])
    ii  A[0] = xor(nodeD[1], xor(nodeB[1], B[0]])
    iii A[1] = nodeB[0]
    iv  B[1] = nodeB[1]
 
6. CD <= xor(nodeD[1], nodeC[1]) + ii + iii + iv
    i   A[0] = xor(nodeD[1], nodeC[1])
    ii  A[1] = xor(nodeC[0], A[0])
    iii B[0] = xor(nodeD[0], A[1])
    iv  B[1] = xor(nodeC[1], B[0])
create_account(self, connection, command)- communicates command, username, and password from client to nodes, and then communicates responses back to client
delete_file(self, filename)- communicates command and filename from client nodes
distribute_data(self, data: bytes, final_chunk=False)
nodeA = chunk0 + chunk2
nodeB = chunk1 + chunk3
nodeC = chunk0 xor chunk1 + chunk2 xor chunk3
nodeE = chunk2 xor chunk1 + chunk0 xor (chunk3 xor chunk3)
find_nodes(self) – finds nodes that are available for connection, and gets their identities
list_all(self, client_connection) – communicates commands from client to nodes and sends the list back
login(self, client_connection)- communicates commands and responses from client to nodes and back
run_protocol(self, client_connection) – executes the communication between client and storage nodes, including file formatting and distribution
to_servers(self, client_connection, filename)
* downloads file to the middleware folder
* uses distribute data to split and xor items into chunks for storage
* makes sure that the file contains a number of chunks divisible by 4
* sends files to the storage nodes
CLASS CLIENT
Methods defined here:
__init__(self, client_socket: socket.socket)
Initialize self.  See help(type(self)) for accurate signature.
client_protocol(self)
create_account(self)
create_credentials(self)
CLASS SERVER
Methods defined here:
__init__(self, csoc: socket.socket, dir_path: str, identity: str, chunk_size: int)
Initialize self.  See help(type(self)) for accurate signature.
create_account(self, username_password) – creates a user directory if it does not yet exist, and sends a confirmation to middleware
list_acc(self) – uses os library to get a list of files and then sends it as padded messages to middleware
login(self, username_password: str) – checks if user directory exists, changes its default directory path to it, and confirms login to middleware. Or not
server_protocol(self) – receives instructions, splits them, controls for broken connections, uses a lot of if  statements to navigate instructions
UTIL.PY
A collection of helper functions
Methods defined here:
Assembly functions used in assemble file function in middleware:
assembleAB(nodes: list, file_a: str, file_b: str)
assembleAC(nodes: list, file_a: str, file_c: str)
assembleAD(nodes: list, file_a: str, file_d: str)
assembleBC(nodes: list, file_b: str, file_c: str)
assembleBD(nodes: list, file_b: str, file_d: str)
assembleCD(nodes: list, file_c: str, file_d: str)
create_chunks(lst) – adds padding to the chunks
cut_chunks(lst) – cuts chunks
end_seq(num: int) – adds ‘xXY’ to the end of chunks
get_chunks(file_name: str) – gets chunks from files before assembly
get_instructions(csoc: socket.socket, chunk_size: int, auto_print: bool = True, auto_decode: bool = True) – receives instructions from sockets
get_pad_chunks(zero_pad_chunks_count: int, chunk_size: int, end_seq) – generates zero chunks of appropriate chunks
pad_message(message: str) – pads messages with zeroes and ‘xXY’ sequence at the end
process_chunks(data: bytes, chunk_size: int)
+ checks if the last chunk needs to be padded
+ pads the last quad of chunks, adding full zero chunks
+ adds info about padding to the end of the file
+ ALWAYS pads, so middleware ALWAYS must cut off padding before sending data to client
receive_file(csoc: socket.socket, file_name: str, chunk_size: int, final_client_file_is_to_be_received=False) – decodes data and stores it until it is confirmed that the next chunk is not a terminating chunk. Then it writes it into file. If the next chunk is a terminating chunk, then it cuts off padding according to the scheme and writes the result into file
send_file(csoc: socket.socket, file_name: str, chunk_size: int) – encodes data and sends it over the socket, until there is not enough data for a whole chunk, and then it executes the padding scheme described for files
send_message(csoc: socket.socket, message: str, chunk_size: int) – sends a padded message over the socket
xor(b1, b2) – XORs two chunks, which must be of equal length (thus padding exists)


 
Process
 
I would like to start by saying, that it is my first project of comparable size. I never had to write a structured application, only individual programs, which definitely did not prepare me for the amount of planning that should have gone into this project prior to writing any code. 
Initially, when the client and server were implemented, send file and receive file were slightly different. They generally had a lot of repeated functionality, and they were not structured into classes. Middleware was started a mere communicator function between the two, but it quickly became obvious, that it is not sustainable
Then any repetitive functionality was standardized and pulled into a util file. Middleware, client, and server were written as highly interconnected programs, with their protocol functions driving development. However, when time came to putting all functions together and testing the operation, it became apparent, that debugging it is simply impossible.
Since I never had to write operational classes, data structures beyond pure formatted data storage and interactions with it were beyond my comprehension. It lead me to researching classes in python, which then was followed by rewriting of most of functions, restructuring padding schemes, and organizing everything into three distinct classes.
However, the application still did not work when put together. This discovery was followed by learning about logging. Thorough rewriting and cleanup of classes guided by logging was extremely effective, as now the application mostly worked, sans major bugs and constant crashes.
Removing them proved tricky. I had to learn how to operate VSCode debugger, and that, combined with continuous logging, finally removed most bugs and made the application somewhat stable. 
Logger, debugger, and pydoc were extremely helpful for this project.
