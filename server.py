import socket, sys, threading, os, queue, time, json, string, random, pickle

from queue import Queue
from block import Block
from prepare import Prepare
from propose import Propose
from promise import Promise
from accepted import Accepted
from decide import Decide
from opRequest import OpRequest
from hashlib import sha256
from time import sleep

#Socket Vars
IP = "127.0.0.1"
processId = None
MY_PORT = None
SERVER_PORTS = []
SERVERS = []
CLIENTS = []
delay = 5

#Paxos Vars
isLeader = False # Tracks if you're leader or not
bNum = (0,0,0) # (depth, seqNum, pid)
acceptNum = (0,0,0) # (depth, seqNum, pid)
acceptVal = None # aka bottom
promises = 0 # Track num of promises
promised = False
receivedB = (0,0,0) # Track highest b received
myVal = None # Track value to propose (your block or received block with highest ballotNum)
accepts = 0 # Track number of accepted
decided = False

#BlockChain Vars
portal = {} # Key-value store
tempOp = Queue(maxsize = 0) # Temporary operations
blockchain = [] # Blockchain aka list of Block objects
master = "" # File to write blockchain to

#blockchain functions _______________________________________________
def addToChain(op, key, hp, nonce, status, val="none"):
    global blockchain
    if val != "none":
        tmpOp = [op, key, val]
    else:
        tmpOp = [op, key]
    tmpBlock = Block(tmpOp, hp, nonce, status)
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
        if block.getHashPtr() is None:
            fString += "None,"
        else:
            fString += block.getHashPtr()
            fString += ","
        fString += block.getNonce()
        fString += ","
        fString += block.getTag()
        if i != len(blockchain) - 1:
            fString += "};"
        else:
            fString += "}"
        i += 1
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
        i += 1

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
        newBlock = Block(fullOp, elems[1], elems[2], elems[3]) # Reconstruct block
        blockchain.append(newBlock) # Add block to blockchain
    #printChain()

def write():
    global master
    f = open(master, "w")
    bcString = buildString()
    f.write(bcString)
    f.flush()

# def tentativeWrite(block):
#     global master
#     f = open(master, "a")
#     tmp = "{"+block.getOpString()+","
#     if block.getHashPtr() is None:
#         tmp += "None,"
#     else:
#         tmp += block.getHashPtr()
#         tmp += ","
#     tmp += block.getNonce()
#     tmp += ","
#     tmp += block.getTag()
#     tmp += "};"
#     f.write(tmp)
#     f.flush()

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
def compareBallots(b1, b2): # Return > 0 if b1 bigger, < 0 if b1 smaller
    if b1[0] == b2[0]: # If depth is same
        if b1[1] == b2[1]: # If seqNum is same
            if b1[2] > b2[2]:
                return 1
            else:
                return -1
        elif b1[1] > b2[1]:
            return 1
        else:
            return -1
    elif b1[0] > b2[0]:
        return 1
    else:
        return -1

def formatOp(op):
    opType = op[0]
    tmp = str(op[0])
    tmp += str(op[1])
    if opType == "put":
        tmp += str(op[2])
    return tmp

# Accept Code_________________________________
def propose(): # Should already be elected
    global tempOp, bNum, promises, receivedB, myVal, promised
    promises = 0 # Reset promises
    opBlock = tempOp.queue[0] # Access first op in queue
    op = formatOp(opBlock) # Concatenate op together
    nonce = calcNonce(op) # Calculate nonce
    #realOp = tempOp.get() # TODO: Might not want to pop yet
    hashVal = calcHashPtr()
    newBlock = None
    if myVal is None: # If all received vals are bottom
        newBlock = Block(opBlock, hashVal, nonce, "tentative")
    else: # If there was a val(s) that was not bottom, use one with highest b
        newBlock = myVal
    msg = Propose("propose", bNum, newBlock)
    pMsg = pickle.dumps(msg)
    broadcastMsg(pMsg)
    receivedB = (0,0,0) # Reset receivedB
    myVal = None # Reset myVal
    promised = False
    # msg = "propose|"+formatBNum(bNum)+"|"+formatOpField([realOp, hashVal, nonce])
    # broadcast(msg)

def accept(b, val):
    global bNum
    if b[0] >= bNum[0]:
        acceptNum = b
        acceptVal = val
        #tentativeWrite(val)
        # Add to chain tentatively
        op = val.getOp()
        hp = val.getHashPtr()
        nonce = val.getNonce()
        if op[0] == "put":
            addToChain(op[0], op[1], hp, nonce, "tentative", op[2])
        else:
            addToChain(op[0], op[1], hp, nonce, "tentative")
        write() # Write to file tentatively
        msg = Accepted("accepted", b, val)
        pMsg = pickle.dumps(msg)
        broadcastMsg(pMsg)
        # TODO: send pMsg to just the leader
        # msg = "accepted|"+formatBNum(b)+"|"+formatOpField(val)
        # send_to_leader(msg)

def calcHashPtr():
    global blockchain
    if len(blockchain) > 0: # If not the first block in the blockchain
        prevBlock = blockchain[-1] # Get previous block
        op = formatOp(prevBlock.getOp()) # Concatenate op
        nonce = prevBlock.getNonce()
        hp = prevBlock.getHashPtr()
        if hp is not None:
            concat = op+nonce+hp # Concatenate string vals of op, nonce, hash
        else: # If previous block was the first block, hash will be None so don't concatenate
            concat = op+nonce
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
            if num <= 2 and num >= 0: # And between 0 and 2
                break
    return nonce

# Decide Code_________________________________
def decide(b, val):
    global accepts, decided
    accepts = 0 # Reset accepts
    op = val.getOp()
    hp = val.getHashPtr()
    nonce = val.getNonce()
    # Append block to blockchain
    if op[0] == "put":
        addToChain(op[0], op[1], hp, nonce, "decided", op[2])
    else:
        addToChain(op[0], op[1], hp, nonce, "decided")
    # Write to file
    write()
    # Update KV
    cMsg = updateKV(op)
    # Remove op from queue
    tempOp.get()
    # Send ack/value to client
    replyClient(cMsg)
    # Broadcast decision to servers
    msg = Decide("decide", b, val)
    pMsg = pickle.dumps(msg)
    broadcastMsg(pMsg)
    decided = False
    #msg = "decide|"+formatBNum(b)+"|"+formatOpField(val)

def updateKV(op):
    global portal
    msg = ""
    if op[0] == "put":
        key = op[1]
        val = op[2]
        portal[key] = val
        printKV()
        msg = "ack"
    else:
        v = portal.get(op[1])
        if v is None:
            msg = "NO_KEY"
        else:
            msg = v
    return msg

def replyClient(msg):
    for sock in CLIENTS:
        sock.sendall(f"{msg}".encode("utf8"))
    # TODO: need to send back to particular client, not all clients

def nonLDecide(b, val):
    global blockchain
    op = val.getOp()
    hp = val.getHashPtr()
    nonce = val.getNonce()
    # Remove tentative block from blockchain
    blockchain.pop()
    # Append decided block to blockchain
    if op[0] == "put":
        addToChain(op[0], op[1], hp, nonce, "decided", op[2])
    else:
        addToChain(op[0], op[1], hp, nonce, "decided")
    write() # Rewrite file 
    # Update KV
    updateKV(op)
    printKV()

#Socket Code____________________________________________

def failProcess():
    MY_SOCK.close()
    for sock in SERVERS: 
        sock.close()
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
        elif "failProcess" in command:
            failProcess()
        elif "failLink" in command:
            parsed = command.replace("(", "").replace(")", "")
            parsed = parsed.lower().replace("faillink", "")
            vals = parsed.split(",")
            src = vals[0]
            dest = vals[1]
            failLink(src, dest)
        elif "fixLink" in command:
            parsed = command.replace("(", "").replace(")", "")
            parsed = parsed.lower().replace("fixlink", "")
            vals = parsed.split(",")
            src = vals[0]
            dest = vals[1]
            fixLink(src, dest)
        elif "printBlockchain" in command:
            printChain()
        elif "printKVStore" in command:
            printKV()
        elif "printQueue" in command:
            printQueue()
        elif command == "broadcast":
            broadcast()
        elif command == "clientBroadcast":
          for sock in CLIENTS:
            sock.sendall(f"test".encode("utf8"))
        elif command == "exit":
            MY_SOCK.close()
            for sock in SERVERS: sock.close()
            os._exit(1)
    return

def broadcastMsg(msg): # Broadcast pickled messages
    sleep(delay)
    for sock in SERVERS:
        sock.sendall(msg)

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
        if not sock in SERVERS:
          CLIENTS.append(sock)

    MY_SOCK.close()

#handles responses from the other SERVERS
def serverResponse(sock, address):
    global accepts, promises, myVal, receivedB, isLeader, decided, promised
    while True:
        #data = sock.recv(1024).decode("utf8")
        data = sock.recv(1024) # NOTE: if we want to receive any strings now, need to separately decode utf8
        if data:
            #print(data)
            dataMsg = pickle.loads(data)
            if isinstance(dataMsg, Prepare): # Receiving PREPARE
                bal = dataMsg.getBNum()
            if isinstance(dataMsg, Promise): # Receiving PROMISE
                ballotNum = dataMsg.getBNum()
                b = dataMsg.getB()
                val = dataMsg.getBlock() # use val.getOp(), val.getHashPtr(), val.getNonce() to get fields
                # If val is None, do nothing (myVal is still your block)
                if val is not None: # If val is not None and b > receivedB, set myVal = val
                    if compareBallots(b, receivedB) > 0:
                        myVal = val
                # Increment promises
                promises += 1
                if promises >= 2 and not promised: # Only need two more, already have own approval
                    promised = True
                    isLeader = True # TODO: Handle tentative/decided fields depending on if leader or not
                    propose() # Is now leader
            if isinstance(dataMsg, Propose): # Receiving PROPOSE (aka ACCEPT)
                b = dataMsg.getBNum()
                val = dataMsg.getBlock()
                accept(b, val)
            if isinstance(dataMsg, Accepted) and isLeader: # Receiving ACCEPTED
                b = dataMsg.getBNum()
                val = dataMsg.getBlock()
                accepts += 1
                if accepts >= 2 and not decided: # Only need two more, already have own approval
                    decided = True
                    decide(b, val)
            if isinstance(dataMsg, Decide): # Receiving DECIDE
                b = dataMsg.getBNum()
                val = dataMsg.getBlock()
                nonLDecide(b, val) # Decide as a participant
            if isinstance(dataMsg, OpRequest): # Receiving request from CLIENT
                op = dataMsg.getOp()
                key = dataMsg.getKey()
                if op == "put":
                    val = dataMsg.getVal()
                    tmpOp = [op, key, val]
                else:
                    tmpOp = [op, key]
                addToQueue(tmpOp)
                isLeader = True
                propose()

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
    master = "persist_"+sys.argv[1]+".txt"

    rebuild() # In case of crash failure, rebuild chain

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