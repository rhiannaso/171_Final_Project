import socket
import sys
import threading
import os
import queue
import time
import json

IP = "127.0.0.1"
FOCUS_PORT = None
SERVER_PORTS = []
SERVERS = {}
SERVER_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#takes stdin commands
def processInput():
    while True:
        command = input()
        if command == "connect":
            connect()
        elif command == "broadcast":
            broadcast()
        elif 'swap' in command:
            swap(command[5:])
        elif command == "exit":
            SERVER_SOCK.close()
            for sock in SERVERS: sock.close()
            os._exit(1)

    return

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

    

#where code waits to receive from server
def clientRequest(sock, id):
    while True:
        data = sock.recv(1024).decode("utf8")
        if(data and id == FOCUS_PORT):
            print(data)
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