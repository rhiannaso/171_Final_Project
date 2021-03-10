class OpRequest:
    def __init__(self, op, key, val="None"):
        self.op = op # String
        self.key = key # String
        self.val = val # Dictionary
    
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