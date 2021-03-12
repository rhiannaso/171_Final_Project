class Leader:
    def __init__(self):
        self.mType = 'leader'
        # self.processId = id
    
    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType

    # def getProcessId(self):
    #     return self.id

    # def setProcessId(self, id):
    #     self.processId= id

class UpdateLeader():
    def __init__(self, port):
        self.port = port
    
    def getPort(self):
        return self.port
    
    def setPort(self, port):
        self.port = port