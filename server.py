import socket, sys, threading, os, queue, time, json, string, random, pickle

from queue import Queue
from block import Block
from prepare import Prepare
from propose import Propose
from promise import Promise
from accepted import Accepted
from decide import Decide
from opRequest import OpRequest
from ballotNum import BallotNum
from clientOp import ClientOp
from hashlib import sha256
from time import sleep
from leader import Leader, UpdateLeader
from links import FailLink, FixLink, TestMsg, FailProcess

#Socket Vars
IP = "127.0.0.1"
processId = None
MY_PORT = None
SERVER_PORTS = []
SERVERS = {}
SERVER_LINKS = {}
CLIENTS = []
delay = 10

#Paxos Vars
isLeader = False # Tracks if you're leader or not
currLeader = None # Tracks current leader by pid
depth = 0 # Tracks length of blockchain
seqNum = 0 # Tracks current sequence number
#bNum = (0,0,0) # (depth, seqNum, pid)
bNum = BallotNum(depth,seqNum,processId)
#acceptNum = (0,0,0) # (depth, seqNum, pid)
acceptNum = BallotNum(0,0,0)
acceptVal = None # aka bottom
promises = 0 # Track num of promises
promised = False
#receivedB = (0,0,0) # Track highest b received
receivedB = BallotNum(0,0,0)
myVal = None # Track value to propose (your block or received block with highest ballotNum)
accepts = 0 # Track number of accepted
decided = False
paxosRun = False # Track if Paxos run is in progress or not

# Locks
queueLock = threading.Lock()
bcLock = threading.Lock()
dictLock = threading.Lock()

#BlockChain Vars
portal = {} # Key-value store
tempOp = Queue(maxsize = 0) # Temporary operations
blockchain = [] # Blockchain aka list of Block objects
master = "" # File to write blockchain to
currLeader = None

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
    i = 0
    while i < tempOp.qsize():
        op = tempOp.queue[i].getFullOp()
        print("OP: ", op[0])
        print("KEY: ", op[1])
        if op[0] == "put":
            print("VAL: ", op[2])
        print("------")
        i += 1

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
    rebuildKV()

def rebuildKV():
    global blockchain, portal
    for block in blockchain:
        op = block.getOp()
        if op[0] == "put":
            key = op[1]
            val = op[2]
            portal[key] = val
    #printKV()

def write():
    global master
    f = open(master, "w")
    bcString = buildString()
    f.write(bcString)
    f.flush()

#Paxos Code____________________________________________

# Helper Code_________________________________
# def compareBallots(b1, b2): # Return > 0 if b1 bigger, < 0 if b1 smaller
#     if b1[0] == b2[0]: # If depth is same
#         if b1[1] == b2[1]: # If seqNum is same
#             if b1[2] > b2[2]:
#                 return 1
#             else:
#                 return -1
#         elif b1[1] > b2[1]:
#             return 1
#         else:
#             return -1
#     elif b1[0] > b2[0]:
#         return 1
#     else:
#         return -1

def formatOp(op):
    opType = op[0]
    tmp = str(op[0])
    tmp += str(op[1])
    if opType == "put":
        tmp += str(op[2])
    return tmp

def printNum(b):
    print("---------------------------")
    print("DEPTH: ", str(b.getDepth()))
    print("NUM: ", str(b.getSeqNum()))
    print("PID: ", str(b.getPid()))
    print("---------------------------")

# Leader Election Code_________________________________

def sendPrepare():
    global bNum
    bNum = BallotNum(bNum.getDepth(), bNum.getSeqNum()+1, bNum.getPid())
    printNum(bNum)
    prepMsg = Prepare('prepare', bNum, MY_PORT)
    print("Sending prepare messages.")
    broadcastMsg(pickle.dumps(prepMsg))

def sendPromise(id):
    promMsg = Promise('promise', bNum, acceptNum, acceptVal)
    print("Sending promise back.")
    if SERVER_LINKS[int(id)]:
        sleep(delay)
        SERVERS[int(id)].sendall(pickle.dumps(promMsg))

# Accept Code_________________________________
def propose(): # Should already be elected
    global tempOp, bNum, promises, receivedB, myVal, promised
    promises = 0 # Reset promises
    opBlock = tempOp.queue[0].getFullOp() # Access first op in queue
    op = formatOp(opBlock) # Concatenate op together
    nonce = calcNonce(op) # Calculate nonce
    hashVal = calcHashPtr()
    newBlock = None
    if myVal is None: # If all received vals are bottom
        newBlock = Block(opBlock, hashVal, nonce, "tentative")
    else: # If there was a val(s) that was not bottom, use one with highest b
        newBlock = myVal
    msg = Propose("propose", bNum, newBlock, currLeader)
    pMsg = pickle.dumps(msg)
    print("Sending ballot proposal messages.")
    broadcastMsg(pMsg)
    receivedB = BallotNum(0,0,0) # Reset receivedB
    myVal = None # Reset myVal
    promised = False

def accept(b, val):
    global bNum, depth, currLeader
    if b.compare(bNum) >= 0: # If b is greater than or equal to ballotNum
        acceptNum = b
        acceptVal = val
        # Add to chain tentatively
        op = val.getOp()
        hp = val.getHashPtr()
        nonce = val.getNonce()
        if op[0] == "put":
            addToChain(op[0], op[1], hp, nonce, "tentative", op[2])
        else:
            addToChain(op[0], op[1], hp, nonce, "tentative")
        depth += 1 # Update depth
        write() # Write to file tentatively
        msg = Accepted("accepted", b, val)
        pMsg = pickle.dumps(msg)
        print(f"Sending accept to current leader: {currLeader}")
        if SERVER_LINKS[int(currLeader)]: # Send accept to leader
            sleep(delay)
            SERVERS[int(currLeader)].sendall(pMsg)

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
        print("Hash Pointer: ", hashPtr.hexdigest())
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
    print("Calculated hash: ", h)
    print("Calculated nonce: ", nonce)
    return nonce

# Decide Code_________________________________
def decide(b, val):
    global accepts, decided, depth, paxosRun
    accepts = 0 # Reset accepts
    op = val.getOp()
    hp = val.getHashPtr()
    nonce = val.getNonce()
    # Append block to blockchain
    if op[0] == "put":
        addToChain(op[0], op[1], hp, nonce, "decided", op[2])
    else:
        addToChain(op[0], op[1], hp, nonce, "decided")
    depth += 1 # Update depth
    write() # Write to file
    cMsg = updateKV(op) # Update KV
    cOp = tempOp.get() # Remove op from queue
    replyClient(cMsg, cOp.getSock()) # Send ack/value to client
    # Broadcast decision to servers
    msg = Decide("decide", b, val)
    pMsg = pickle.dumps(msg)
    print("Sending decision messages.")
    broadcastMsg(pMsg)
    decided = False
    paxosRun = False

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

def replyClient(msg, sock):
    sleep(delay)
    sock.sendall(f"{msg}".encode("utf8"))

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
    updateKV(op) # Update KV

#Socket Code____________________________________________

def failProcess():
    #MY_SOCK.close()
    sleep(delay)
    for sock in SERVERS: 
        SERVERS[sock].sendall(pickle.dumps(FailProcess(int(MY_PORT))))
        SERVERS[sock].close()
    MY_SOCK.close()
    os._exit(1)

def failLink(src, dest):
    SERVER_LINKS[int(dest)] = False
    sleep(delay)
    SERVERS[int(dest)].sendall(pickle.dumps(FailLink(src, dest)))
    return

def fixLink(src, dest):
    SERVER_LINKS[int(dest)] = True
    sleep(delay)
    SERVERS[int(dest)].sendall(pickle.dumps(FixLink(src, dest)))
    return

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
        elif command == "currLeader":
            print(currLeader)
        elif command == "clientBroadcast":
          for sock in CLIENTS:
            sock.sendall(f"test".encode("utf8"))
        elif command == "exit":
            MY_SOCK.close()
            for sock in SERVERS: SERVERS[sock].close()
            os._exit(1)
    return

def broadcastMsg(msg): # Broadcast pickled messages
    sleep(delay)
    for id in SERVERS:
        if SERVER_LINKS[id]:
            SERVERS[id].sendall(msg)

def broadcast():
    for id in SERVERS:
        if SERVER_LINKS[id]:
            SERVERS[id].sendall(pickle.dumps(TestMsg(f"Broadcast Received from Server {processId}")))

#connects to other SERVERS
def connect():
    for id in SERVER_PORTS:
        if id != MY_PORT:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address = (socket.gethostname(), id)
            sock.connect(address)
            print("Connected to " + str(id))
            SERVERS[id] = sock
            SERVER_LINKS[id] = True

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
    global accepts, promises, myVal, receivedB, isLeader, decided, promised, paxosRun, bNum, currLeader
    while True:
        #data = sock.recv(1024).decode("utf8")
        data = sock.recv(1024) # NOTE: if we want to receive any strings now, need to separately decode utf8
        if data:
            #print(data)
            dataMsg = pickle.loads(data)
            if isinstance(dataMsg, OpRequest): # Receiving request from CLIENT
                print("Receiving client request.")
                dataMsg.setSock(sock)
                if(dataMsg.getResetLeader()):
                    currLeader = None
                if not isLeader: # If current server is not the leader
                    if currLeader is None: # If not leader and there is no leader
                        print("Trying to get elected.")
                        addToQueue(dataMsg) # TODO: Figure out when to add to queue to deal with concurrent leader requests
                        sendPrepare()
                    else: # Forward opRequest to actual leader
                        print("Forward request to leader.")
                        msg = f"leader|{currLeader}"
                        sleep(delay)
                        sock.sendall(msg.encode("utf8"))
                else: # If current server is already the leader
                    addToQueue(dataMsg)
                    print("I am already the leader.")
                    while not tempOp.empty() and isLeader:
                        if not paxosRun:
                            paxosRun = True
                            propose()
            if isinstance(dataMsg, Leader): # Receiving LEADER
                sendPrepare()
            if isinstance(dataMsg, Prepare): # Receiving PREPARE
                print("Receiving a prepare message.")
                bal = dataMsg.getBNum()
                if bal.compare(bNum) > -1:
                    bNum = bal
                    isLeader = False # Ensure that you're not leader if you're promising
                    sendPromise(dataMsg.getProcessId())
            if isinstance(dataMsg, Promise): # Receiving PROMISE
                print("Receiving a promise.")
                ballotNum = dataMsg.getBNum()
                b = dataMsg.getB()
                val = dataMsg.getBlock()
                # If val is None, do nothing (myVal is still your block)
                if val is not None: # If val is not None and b > receivedB, set myVal = val
                    if b.compare(receivedB) >= 0:
                        myVal = val
                # Increment promises
                promises += 1
                if promises >= 2 and not promised: # Only need two more, already have own approval
                    promised = True
                    isLeader = True
                    print("I am now the leader.")
                    currLeader = MY_PORT
                    broadcastMsg(pickle.dumps(UpdateLeader(MY_PORT)))
                    while not tempOp.empty() and isLeader: # Is now leader, run until queue is empty
                        if not paxosRun:
                            paxosRun = True # Ensure paxos only runs on one op at a time
                            propose()
            if isinstance(dataMsg, UpdateLeader):
                currLeader = dataMsg.getPort()
                # while not tempOp.empty() and not isLeader: # Empty out queue if not leader
                #     print("Forwarding to the actual leader.")
                #     clientSock = tempOp.get().getSock()
                #     msg = f"leader|{currLeader}"
                #     clientSock.sendall(msg.encode("utf8"))
            if isinstance(dataMsg, Propose): # Receiving PROPOSE (aka ACCEPT)
                print("Receiving a ballot proposal.")
                b = dataMsg.getBNum()
                val = dataMsg.getBlock()
                if currLeader is None:
                    currLeader = dataMsg.getCurrLeader()
                accept(b, val)
            if isinstance(dataMsg, Accepted): # Receiving ACCEPTED
                print("Receiving an accepted message.")
                b = dataMsg.getBNum()
                val = dataMsg.getBlock()
                accepts += 1
                if accepts >= 2 and not decided: # Only need two more, already have own approval
                    decided = True
                    decide(b, val)
            if isinstance(dataMsg, Decide): # Receiving DECIDE
                print("Receiving a decision.")
                b = dataMsg.getBNum()
                val = dataMsg.getBlock()
                nonLDecide(b, val) # Decide as a participant
            if isinstance(dataMsg, FailLink):
                SERVER_LINKS[int(dataMsg.getSrc())] = False
            if isinstance(dataMsg, FixLink):
                SERVER_LINKS[int(dataMsg.getSrc())] = True
            if isinstance(dataMsg, FailProcess):
                SERVERS.pop(int(dataMsg.getPort()), None)
            if isinstance(dataMsg, TestMsg):
                print(dataMsg.getMsg())

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
    bNum = BallotNum(depth,seqNum,processId)

    if os.path.isfile(master):
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