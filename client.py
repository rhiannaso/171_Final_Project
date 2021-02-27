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
SERVERS = []
SERVER_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#takes stdin commands
def processInput():
    while True:
        command = input()
        if command == "connect":
            connect()
        elif command == "broadcast":
            broadcast()
        elif command == "exit":
            SERVER_SOCK.close()
            for sock in SERVERS: sock.close()
            os._exit(1)

    return

def broadcast():
        SERVER_SOCK.sendall(f"Broadcast Received from Client".encode("utf8"))

#connects to other SERVERS
def connect():
    for id in SERVER_PORTS:
        if id != FOCUS_PORT:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address = (socket.gethostname(), id)
            sock.connect(address)
            print("Connected to Server with Port " + str(id))
            SERVERS.append(sock)
        elif id == FOCUS_PORT:
            address = (socket.gethostname(), id)
            SERVER_SOCK.connect(address)
            print("Connect with Primary Server " + str(id))

    threading.Thread(target=clientRequest).start()

#where code waits to receive from server
def clientRequest():
    print("entered Loop")
    while True:
        data = SERVER_SOCK.recv(1024).decode("utf8")
        if(data):
            print(data)
        if not data:
            sock.close()
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