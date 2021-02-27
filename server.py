import socket
import sys
import threading
import os
import queue
import time
import json

from queue import Queue
from block import Block

IP = "127.0.0.1"
processId = None
MY_PORT = None
SERVER_PORTS = []
SERVERS = []

#BlockChain Vars
portal = {} # Key-value store
tempOp = Queue(maxsize = 0) # Temporary operations
blockchain = [] # Blockchain aka list of Block objects
master = "persist.txt" # File to write blockchain to TODO: generate separate file per server


#blockchain functions _______________________________________________
def addToChain(op, key, hp, nonce, val="none"):
  global blockchain
  if val != "none":
    tmpOp = [op, key, val]
  else:
    tmpOp = [op, key]
  tmpBlock = Block(tmpOp, hp, nonce, "tentative") # TODO: if decide received from leader, set to "decided"
  blockchain.append(tmpBlock)

def buildString():
  global blockchain
  fString = ""
  i = 0
  for block in blockchain:
    fString += "{"
    fString += block.getOpString()
    fString += ","
    fString += block.getHashPtr()
    fString += ","
    fString += block.getNonce()
    if i != len(blockchain) - 1:
      fString += "};"
    else:
      fString += "}"
    i += 1
    # TODO: Add additional field for tentative vs. decided
  return fString

def printChain():
  global blockchain
  i = 0
  for block in blockchain:
    print("------")
    print("BLOCK ", str(i))
    print("OP: ", block.getOpString())
    print("HASH POINTER: ", block.getHashPtr())
    print("NONCE: ", block.getNonce())
    print("TAG: ", block.getTag())
    print("------")

def rebuild():
  global master, blockchain
  blockchain.clear() # Clear out inconsistent blockchain
  f = open(master, "r")
  blockContent = f.readlines()
  blocks = blockContent[0].split(";")
  for block in blocks:
    block = block.strip("{}") # Strip braces off block
    elems = block.split(",")
    fullOp = elems[0].strip("<>").split("|") # Strip op surroundings
    newBlock = Block(fullOp, elems[1], elems[2], "tentative") # Reconstruct block TODO: if decide received from leader, set to "decided"
    blockchain.append(newBlock) # Add block to blockchain
  printChain()

def write():
  global master
  f = open(master, "w")
  bcString = buildString()
  f.write(bcString)
  f.flush()

#____________________________________________

#takes stdin commands
def processInput():
    while True:
        command = input()
        if command == "connect":
            connect()
        elif command == "broadcast":
            broadcast()
        elif command == "exit":
            MY_SOCK.close()
            for sock in SERVERS: sock.close()
            os._exit(1)
        elif command == "build":
            addToChain(
            "put", 
            "1234567", 
            "1234567812345678123456781234567812345678123456781234567812345678", 
            "0",
            {"phone_number": "111-222-3333"}
            )
            addToChain(
            "get", 
            "7654321", 
            "87654321ABCDEF9087654321ABCDEF9087654321ABCDEF9087654321ABCDEF90", 
            "1"
            )
            addToChain(
            "get", 
            "5555555", 
            "ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01", 
            "2"
            )
            write()
            printChain()
        elif command == "rebuild":
            rebuild()

    return

def broadcast():
    for sock in SERVERS:
        sock.sendall(f"Broadcast Received from Server {processId}".encode("utf8"))

#connects to other SERVERS
def connect():
    for id in SERVER_PORTS:
        if id != MY_PORT:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address = (socket.gethostname(), id)
            sock.connect(address)
            print("Connected to " + str(id))
            SERVERS.append(sock)

    threading.Thread(target=serverRequest).start()

#listen for server connections
def serverListener():
    MY_SOCK.listen(32)
    while True:
        sock, address = MY_SOCK.accept()
        threading.Thread(target=serverResponse, args=(sock, address)).start()

    MY_SOCK.close()

#handles responses from the other SERVERS
def serverResponse(sock, address):
    while True:
        data = sock.recv(1024).decode("utf8")
        if(data):
            print(data)
        if not data:
            sock.close()
            break

#where code sits after connecting
def serverRequest():
    while True:
        pass
    return


if __name__ == '__main__':
    processId = int(sys.argv[1])

    #reads config file for other client ports
    with open('./config.json') as configs:
        clientPortDict = json.load(configs)
    MY_PORT = clientPortDict[str(processId)]

    for i in clientPortDict.keys():
        SERVER_PORTS.append(clientPortDict[i])

    #create 'server' of the current client
    MY_SOCK = socket.socket()
    MY_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    MY_SOCK.bind((socket.gethostname(), MY_PORT))

    threading.Thread(target=serverListener).start()

    processInput()