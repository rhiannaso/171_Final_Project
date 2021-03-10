class BallotNum:
    def __init__(self, depth, seqNum, pid):
        self.depth = depth # Int
        self.seqNum = seqNum # Int
        self.pid = pid # Int
    
    def getDepth(self):
        return self.depth

    def setDepth(self, depth):
        self.depth = depth

    def getSeqNum(self):
        return self.seqNum
    
    def setSeqNum(self, seqNum):
        self.seqNum = seqNum

    def getPid(self):
        return self.pid

    def setPid(self, pid):
        self.pid = pid

    def compare(self, otherNum):
        if self.depth == otherNum.getDepth(): # If depth is same
            if self.seqNum == otherNum.getSeqNum(): # If seqNum is same
                if self.pid > otherNum.getPid():
                    return 1
                elif self.pid < otherNum.getPid():
                    return -1
                else:
                    return 0
            elif self.seqNum > otherNum.getSeqNum():
                return 1
            else:
                return -1
        elif self.depth > otherNum.getDepth():
            return 1
        else:
            return -1