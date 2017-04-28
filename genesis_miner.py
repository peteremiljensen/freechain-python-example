from block import *
import datetime

loaves = []
previous_block = "-1"
height = 0
nounce = 0
block = None
while True:
    timestamp = str(datetime.datetime.now())
    block = Block(loaves, height, previous_block, timestamp, nounce)
    #print(block.get_hash()[:5])
    if block.get_hash()[:4] == '0000':
        print (block.json())
        break
    nounce += 1
