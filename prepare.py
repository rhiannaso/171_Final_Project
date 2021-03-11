from ballotNum import BallotNum

class Prepare:
    def __init__(self, mType, bNum, processId):
        self.mType = mType # String
        self.bNum = bNum # BallotNum
        self.processId = processId

    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType

    def getBNum(self):
        return self.bNum
    
    def setBNum(self, bNum):
        self.bNum = bNum
        
    def getProcessId(self):
        return self.processId

    def setProcessId(self, id):
        self.processId= id