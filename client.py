import socket, sys, threading, os, queue, time, json, pickle
from queue import Queue
from opRequest import OpRequest
from leader import Leader
import time
import random

IP = "127.0.0.1"
FOCUS_PORT = None
SERVER_PORTS = []
SERVERS = {}
SERVER_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientOp = Queue(maxsize = 0) # Operations to send
receivedResponse = False
timerActive = False

#takes stdin commands
def processInput():
    while True:
        command = input()
        if command == "connect":
            connect()
        elif command == "broadcast":
            broadcast()
        elif command == "leader":
            SERVERS[FOCUS_PORT].sendall(pickle.dumps(Leader()))
        elif command == 'leader':
            SERVERS[FOCUS_PORT].sendall(Leader())
        elif 'swap' in command:
            swap(command[5:])
        elif command == "exit":
            SERVER_SOCK.close()
            for sock in SERVERS: SERVERS[sock].close()
            os._exit(1)
        elif "operation" in command.lower():
            parsed = command.replace("(", "").replace(")", "")
            parsed = parsed.lower().replace("operation", "")
            vals = parsed.split(",")
            op = vals[0].strip()
            key = vals[1].strip()
            req = OpRequest(op, key, False)
            if op == "put":
                val = vals[2].strip()
                req = OpRequest(op, key, False, val)
            clientOp.put(req)
            if clientOp.qsize() == 1: # Only spawn thread if first operation
                threading.Thread(target=handleOp).start()
            #msg = pickle.dumps(req)
            #SERVERS[FOCUS_PORT].sendall(msg)

    return

def handleOp():
    global clientOp, receivedResponse
    if clientOp.qsize() == 1: # If first op in queue, don't need to wait for response
        receivedResponse = True
    while not clientOp.empty():
        if receivedResponse and not clientOp.empty():
            req = clientOp.queue[0]
            msg = pickle.dumps(req)
            SERVERS[FOCUS_PORT].sendall(msg)

            
            threading.Thread(target=timer, args=()).start()

            receivedResponse = False

def swap(PORT):
    global FOCUS_PORT
    FOCUS_PORT = int(PORT)
    print("Primary Server Swapped to PORT " + str(PORT))

def broadcast():
    SERVERS[FOCUS_PORT].sendall(f"Broadcast Received from Client".encode("utf8"))
    print(FOCUS_PORT)

#connects to other SERVERS
def connect():
    for id in SERVER_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = (socket.gethostname(), id)
        sock.connect(address)
        SERVERS[id] = sock
        threading.Thread(target=clientRequest, args=(sock,id)).start()
        if id != FOCUS_PORT:
            print("Connected to Server with Port " + str(id))
        elif id == FOCUS_PORT:
            print("Connect with Primary Server " + str(id))

def timer():
    global timerActive
    timerActive = True
    timeLeft = 60
    while timeLeft > 0:
        if timerActive:
            print(timeLeft)
            time.sleep(1)
            timeLeft -= 1
        else:
            return
    
    timerActive = False
    req = clientOp.queue[0]
    req.setResetLeader(True)
    msg = pickle.dumps(req)
    #random port swap
    print("swapping")
    swap(randomPort())
    SERVERS[FOCUS_PORT].sendall(msg)
    threading.Thread(target=timer, args=()).start()


def randomPort():
    keys = list(SERVERS.keys())
    while(True):
        newPort = keys[random.randrange(len(keys))]
        if newPort != FOCUS_PORT:
            return newPort

#where code waits to receive from server
def clientRequest(sock, id):
    global receivedResponse, timerActive
    while True:
        data = sock.recv(1024).decode("utf8")
        timerActive = False
        if(data and id == FOCUS_PORT):
            if "leader" in data: # Changing leaders and forwarding
                server_id = data.split("|")[1]
                print(server_id)
                swap(server_id)
                req = clientOp.queue[0]
                msg = pickle.dumps(req)
                SERVERS[FOCUS_PORT].sendall(msg)

                timerActive = True
                threading.Thread(target=timer, args=()).start()
            else: # Getting response from server
                clientOp.get() # Pop off operation
                receivedResponse = True
                print(data)
        # if data:
        #     print(data)
        if not data:
            break
    return

if __name__ == '__main__':
    FOCUS_PORT = int(sys.argv[1])

    #reads config file for other client ports
    with open('./config.json') as configs:
        clientPortDict = json.load(configs)

    for i in clientPortDict.keys():
        SERVER_PORTS.append(clientPortDict[i])

    processInput()