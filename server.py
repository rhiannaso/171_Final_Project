import socket, sys, threading, os, queue, time, json, string, random

from queue import Queue
from block import Block
from hashlib import sha256

#Socket Vars
IP = "127.0.0.1"
processId = None
MY_PORT = None
SERVER_PORTS = []
SERVERS = []
CLIENTS = []

#Paxos Vars
bNum = (0,0,0)
acceptNum = (0,0,0)
acceptVal = None # aka bottom
promises = {} # Track num of promises
accepts = {} # Track number of accepted

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

def addToQueue(op):
    tempOp.put(op)

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

def printKV():
    global portal
    for key in portal:
        print("KEY: ", key)
        print("VAL: ", portal[key])
        print("------")

def printQueue():
    global tempOp
    while not tempOp.empty():
        op = tempOp.get()
        print("OP: ", op[0])
        print("KEY: ", op[1])
        if op[0] == "put":
            print("VAL: ", op[2])
        print("------")

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

def inputBuild():
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


#Paxos Code____________________________________________

# Helper Code_________________________________
def formatBNum(b):
    return b[0]+","+b[1]+","+b[2]

def formatOpField(val):
    opType = val[0][0]
    v = ""
    if opType == "put":
        v = f',{val[0][2]}'
    tmp = f'{opType},{val[0][1]}{v};{val[1]},{val[2]}'
    return tmp

def formatOp(op):
    opType = op[0]
    tmp = str(op[0])
    tmp += ","
    tmp += str(op[1])
    if opType == "put":
        tmp += ","
        tmp += str(op[2])
    return tmp

# Accept Code_________________________________
def propose(): # Should already be elected 
    global tempOp, bNum
    opBlock = tempOp.queue[0] # Access first op in queue
    op = formatOp(opBlock).replace(",")
    nonce = calcNonce(op) # Calculate nonce
    realOp = tempOp.get() # TODO: Might not want to pop yet
    hashVal = calcHashPtr()
    newBlock = Block(realOp, hashVal, nonce, "tentative") # TODO: Change so not always tentative
    msg = "propose|"+formatBNum(bNum)+"|"+formatOpField([realOp, hashVal, nonce])
    # broadcast(msg)

def accept(b, val):
    global bNum
    if b[0] >= bNum[0]:
        acceptNum = b
        acceptVal = Block(val[0], val[1], val[2], "tentative") # TODO: Change so not always tentative
        msg = "accepted|"+formatBNum(b)+"|"+formatOpField(val)
        # send_to_leader(msg)

def calcHashPtr():
    global blockchain
    if len(blockchain) > 0: # If not the first block in the blockchain
        prevBlock = blockchain[-1] # Get previous block
        op = prevBlock.getOpString().replace("<", "").replace(">", "").replace("|", "")
        nonce = prevBlock.getNonce()
        hp = prevBlock.getHashPtr()
        concat = op+nonce+hp # Concatenate string vals of op, nonce, hash
        hashPtr = sha256(concat.encode()) # Calculate hash
        return hashPtr.hexdigest()
    else: # If first block in blockchain
        return None

def calcNonce(op):
    nonce = ""
    N = 5 # Length of random string
    while True:
        nonce = ''.join(random.choices(string.ascii_uppercase + string.digits, k = N))
        hashStr = op+nonce
        h = sha256(hashStr.encode()).hexdigest()
        if h[-1].isdigit(): # If the last character is a digit
            num = int(h[-1])
            if num <= 2 and num >= 0: # And less between 0 and 2
                break
    return nonce

# Decide Code_________________________________
def decide(b, val):
    # Append block to blockchain
    if val[0][0] == "put":
        addToChain(val[0][0], val[0][1], val[1], val[2], val[0][2])
    else:
        addToChain(val[0][0], val[0][1], val[1], val[2])
    # Update KV
    cMsg = updateKV(val)
    # Remove op from queue
    tempOp.get()
    # Send ack/value to client
    replyClient(cMsg)
    # Broadcast decision to servers
    msg = "decide|"+formatBNum(b)+"|"+formatOpField(val)
    # broadcast(msg)

def updateKV(val):
    global portal
    msg = ""
    if val[0][0] == "put":
        key = val[0][1]
        v = val[0][2]
        portal[key] = v
        printKV()
        msg = "ack"
    else:
        v = portal.get(val[0][1])
        if v is None:
            msg = "NO_KEY"
        else:
            msg = v
    return msg

def replyClient(msg):
    for sock in CLIENTS:
        sock.sendall(f"{msg}".encode("utf8"))

def nonLDecide(b, val):
    # Append block to blockchain
    if val[0][0] == "put":
        addToChain(val[0][0], val[0][1], val[1], val[2], val[0][2])
    else:
        addToChain(val[0][0], val[0][1], val[1], val[2])
    # Update KV
    updateKV(val)
    printKV()

#Socket Code____________________________________________

def failProcess():
    MY_SOCK.close()
    os._exit(1)

def failLink(src, dest):
    return # TODO: stub

def fixLink(src, dest):
    return # TODO: stub

#takes stdin commands
def processInput():
    while True:
        command = input()
        if command == "connect":
            connect()
        elif command == "broadcast":
            broadcast()
        elif command == "clientBroadcast":
          for sock in CLIENTS:
            sock.sendall(f"test".encode("utf8"))
        elif command == "exit":
            MY_SOCK.close()
            for sock in SERVERS: sock.close()
            os._exit(1)
        elif command == "build":
            inputBuild()
        elif command == "rebuild":
            rebuild()
        elif command == "queue": # TEMP: Used to demo adding to queue
          tempOp = ["get", "1234567"]
          addToQueue(tempOp)
          tempOp = ["put", "7654321", {"phone_number": "111-222-3333"}]
          addToQueue(tempOp)
          printQueue()
        elif command == "dict": # TEMP: used to demo adding to key-value store
          key = "1234567"
          val = {"phone_number": "111-222-3333"}
          portal[key] = val
          printKV()

    return

def broadcast(): # TODO: alter broadcast so message can be passed as param to be broadcast
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
        if not sock in SERVERS:
          CLIENTS.append(sock)

    MY_SOCK.close()

# Handles received string data and recreates vals
def parseBVal(data, pType):
    if pType == "promise":
        tmp = data.split("|")
        tmpB = tmp[1].split(",")
        ballotNum = (tmpB[0], tmpB[1], tmpB[2])
        tmpB2 = tmp[2].split(",")
        b = (tmpB2[0], tmpB2[1], tmpB2[2])
        tmpVal = tmp[3].split(";")
        op = tmpVal[0].split(",")
        other = tmpVal[1].split(",")
        val = [[op[0], op[1], op[2]], other[0], other[1]]
        return (ballotNum, b, val)
    else:
        tmp = data.split("|")
        tmpB = tmp[1].split(",")
        b = (tmpB[0], tmpB[1], tmpB[2])
        tmpVal = tmp[2].split(";")
        op = tmpVal[0].split(",")
        other = tmpVal[1].split(",")
        val = [[op[0], op[1], op[2]], other[0], other[1]]
        return (b, val)

#handles responses from the other SERVERS
def serverResponse(sock, address):
    while True:
        data = sock.recv(1024).decode("utf8")
        if data:
            print(data)
            if "promise" in data: # Assume promise|seqNum,pid,depth|b_seqNum,b_pid,b_depth|op,key,val;hash,nonce
                parsedVals = parseBVal(data, "promise")
                ballotNum = parsedVals[0]
                b = parsedVals[1]
                val = parsedVals[2]
                # TODO: Figure out how to store both b and val so that later we can check if all val are bottom and see which b is biggest
                # If size of promises >= majority: is now leader and propose()
            if "propose" in data: # Assume propose|seqNum,pid,depth|op,key,val;hash,nonce
                parsedVals = parseBVal(data, "propose")
                b = parsedVals[0]
                val = parsedVals[1]
                # Clear promises?
            if "accepted" in data: # Assume accepted|seqNum,pid,depth|op,key,val;hash,nonce
                parsedVals = parseBVal(data, "accepted")
                b = parsedVals[0]
                val = parsedVals[1]
                # Add to accepts
                # If size of accepts >= majority: decide(b, val)
            if "decide" in data: # Assume decide|seqNum,pid,depth|op,key,val;hash,nonce
                parsedVals = parseBVal(data, "decide")
                b = parsedVals[0]
                val = parsedVals[1]
                nonLDecide(b, val)
                # Clear accepts?
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