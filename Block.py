class Block:
  def __init__(self, op, hp, nonce, tag):
    self.op = op[:] # List of op, key, val
    self.hp = hp # String
    self.nonce = nonce # String
    self.tag = tag # String

  def getOpType(self):
    return self.op[0]

  def getOp(self):
    return self.op

  def setOp(self, op, key, val="none"):
    if val == "none": # If get op
      self.op = [op, key]
    else: # If put op
      self.op = [op, key, val]

  def getOpString(self):
    opType = self.getOpType()
    tmp = "<"
    tmp += str(self.op[0])
    tmp += "|"
    tmp += str(self.op[1])
    if opType == "put":
      tmp += "|"
      tmp += str(self.op[2])
    tmp += ">"
    return tmp

  def getHashPtr(self):
    return self.hp

  def setHashPtr(self, hp):
    self.hp = hp

  def getNonce(self):
    return self.nonce

  def setNonce(self, nonce):
    self.nonce = nonce

  def getTag(self):
    return self.tag

  def setTag(self, tag):
    self.tag = tag