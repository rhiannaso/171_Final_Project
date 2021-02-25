import socket
import sys
import threading
import os
import queue
import time
import json

IP = "127.0.0.1"
processId = None
MY_PORT = None
SERVER_PORTS = []
SERVERS = []

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
        print(data)
    sock.close()

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