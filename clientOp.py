import socket

class ClientOp:
    def __init__(self, sock, op):
        self.sock = sock # Socket
        self.op = op # List [op, key, val]
    
    def getSock(self):
        return self.sock

    def setSock(self, sock):
        self.sock = sock

    def getFullOp(self):
        return self.op
    
    def setFullOp(self, op):
        self.op = op

    def getOp(self):
        return self.op[0]
    
    def getKey(self):
        return self.op[1]

    def getVal(self):
        if self.op[0] == "put":
            return self.op[2]