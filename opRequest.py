import socket

class OpRequest:
    def __init__(self, op, key, val="None"):
        self.op = op # String
        self.key = key # String
        self.val = val # Dictionary
        self.sock = None

    def getFullOp(self):
        if self.op == "put":
            return [self.op, self.key, self.val]
        else:
            return [self.op, self.key]
    
    def getOp(self):
        return self.op

    def setOp(self, op):
        self.op = op

    def getKey(self):
        return self.key
    
    def setKey(self, key):
        self.key = key

    def getVal(self):
        return self.val

    def setVal(self, val):
        self.val = val

    def getSock(self):
        return self.sock

    def setSock(self, sock):
        self.sock = sock