import socket
import sys
import threading
import os
import queue
import time
import json

IP = "127.0.0.1"
processId = None
SERVER_PORT = None
MY_PORT = None
SERVER_PORTS = []
CLIENTS = []

#takes stdin commands
def processInput():
    while True:
        command = input()
        if command == "connect":
            connect()
        elif command == "broadcast":
            broadcast()
        elif command == "exit":
            os._exit(1)

    return

def broadcast():
    for sock in CLIENTS:
        sock.sendall(f"Broadcast Received from Server {processId}".encode("utf8"))

#connects to other clients
def connect():
    for id in SERVER_PORTS:
        if id != MY_PORT:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address = (socket.gethostname(), id)
            sock.connect(address)
            print("Connected to " + str(id))
            CLIENTS.append(sock)

    threading.Thread(target=clientRequest).start()

#listen for client connections
def clientListener():
    MY_SOCK.listen(32)
    while True:
        sock, address = MY_SOCK.accept()
        threading.Thread(target=clientResponse, args=(sock, address)).start()

    MY_SOCK.close()

#handles responses from the other clients
def clientResponse(sock, address):
    while True:
        data = sock.recv(1024).decode("utf8")
        print(data)
    sock.close()

#where code sits after connecting
def clientRequest():
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

    threading.Thread(target=clientListener).start()

    processInput()