from block import Block

class Propose:
    def __init__(self, mType, bNum, val):
        self.mType = mType # String
        self.bNum = bNum # Tuple: (depth, seqNum, pid)
        self.val = val # Block: op (list), hash (string), none (string)
    
    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType

    def getBNum(self):
        return self.bNum
    
    def setBNum(self, bNum):
        self.bNum = bNum

    def getBlock(self):
        return self.val

    def setBlock(self, val):
        self.val = val