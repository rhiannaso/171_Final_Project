from block import Block
from ballotNum import BallotNum

class Promise:
    def __init__(self, mType, bNum, b, val):
        self.mType = mType # String
        self.bNum = bNum # BallotNum
        self.b = b # BallotNum
        self.val = val # Block: op (list), hash (string), none (string)
    
    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType

    def getBNum(self):
        return self.bNum
    
    def setBNum(self, bNum):
        self.bNum = bNum

    def getB(self):
        return self.b

    def setB(self, b):
        self.b = b

    def getBlock(self):
        return self.val

    def setBlock(self, val):
        self.val = val