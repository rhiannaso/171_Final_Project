class Prepare:
    def __init__(self, mType, bNum):
        self.mType = mType # String
        self.bNum = bNum # Tuple: (depth, seqNum, pid)
    
    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType

    def getBNum(self):
        return self.bNum
    
    def setBNum(self, bNum):
        self.bNum = bNum