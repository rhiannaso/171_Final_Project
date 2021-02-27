from queue import Queue
from block import Block

portal = {} # Key-value store
tempOp = Queue(maxsize = 0) # Temporary operations
blockchain = [] # Blockchain aka list of Block objects
master = "persist.txt" # File to write blockchain to TODO: generate separate file per server

def addToChain(op, key, hp, nonce, val="none"):
  global blockchain
  if val != "none":
    tmpOp = [op, key, val]
  else:
    tmpOp = [op, key]
  tmpBlock = Block(tmpOp, hp, nonce, "tentative") # TODO: if decide received from leader, set to "decided"
  blockchain.append(tmpBlock)

def buildString():
  global blockchain
  fString = ""
  i = 0
  for block in blockchain:
    fString += "{"
    fString += block.getOpString()
    fString += ","
    fString += block.getHashPtr()
    fString += ","
    fString += block.getNonce()
    if i != len(blockchain) - 1:
      fString += "};"
    else:
      fString += "}"
    i += 1
    # TODO: Add additional field for tentative vs. decided
  return fString

def printChain():
  global blockchain
  i = 0
  for block in blockchain:
    print("------")
    print("BLOCK ", str(i))
    print("OP: ", block.getOpString())
    print("HASH POINTER: ", block.getHashPtr())
    print("NONCE: ", block.getNonce())
    print("TAG: ", block.getTag())
    print("------")

def rebuild():
  global master, blockchain
  blockchain.clear() # Clear out inconsistent blockchain
  f = open(master, "r")
  blockContent = f.readlines()
  blocks = blockContent[0].split(";")
  for block in blocks:
    block = block.strip("{}") # Strip braces off block
    elems = block.split(",")
    fullOp = elems[0].strip("<>").split("|") # Strip op surroundings
    newBlock = Block(fullOp, elems[1], elems[2], "tentative") # Reconstruct block TODO: if decide received from leader, set to "decided"
    blockchain.append(newBlock) # Add block to blockchain
  printChain()

def write():
  global master
  f = open(master, "w")
  bcString = buildString()
  f.write(bcString)
  f.flush()

if __name__ == "__main__":
  cmd = input()
  if cmd == "build":
    addToChain(
      "put", 
      "1234567", 
      "1234567812345678123456781234567812345678123456781234567812345678", 
      "0",
      {"phone_number": "111-222-3333"}
    )
    addToChain(
      "get", 
      "7654321", 
      "87654321ABCDEF9087654321ABCDEF9087654321ABCDEF9087654321ABCDEF90", 
      "1"
    )
    addToChain(
      "get", 
      "5555555", 
      "ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01ABCDEF01", 
      "2"
    )
    write()
    printChain()
  elif cmd == "rebuild":
    rebuild()
  else:
    pass
  
  