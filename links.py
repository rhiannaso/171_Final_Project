class FailProcess:
    def __init__(self, port):
        self.port = port

    def setPort(self, port):
        self.port = port

    def getPort(self):
        return self.port

class FailLink:
    def __init__(self, src, dest):
        self.mType = 'failLink'
        self.src = src
        self.dest = dest
    
    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType
    
    def getSrc(self):
        return self.src
    
    def getDest(self):
        return self.dest

class FixLink:
    def __init__(self, src, dest):
        self.mType = 'fixLink'
        self.src = src
        self.dest = dest
    
    def getType(self):
        return self.mType

    def setType(self, mType):
        self.mType = mType
    
    def getSrc(self):
        return self.src
    
    def getDest(self):
        return self.dest

class TestMsg:
    def __init__(self, msg):
        self.mType = 'testmsg'
        self.msg = msg
    
    def setMsg(self, msg):
        self.msg = msg
    
    def getMsg(self):
        return self.msg