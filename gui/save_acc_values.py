from bluepy import btle
from struct import *
import binascii
import datetime as dt
import numpy as np
import datetime as dt
import os

cwd=os.getcwd()

 
print ("Connecting...")
dev = btle.Peripheral("CB:A4:4C:2E:E6:B8", btle.ADDR_TYPE_RANDOM)
 
print ("Services...")
for svc in dev.services:
    print (str(svc))

service=dev.getServiceByUUID('02366e80-cf3a-11e1-9ab4-0002a5d5c51b')

print ("Characteristics...")
char=service.getCharacteristics('340a1b80-cf4b-11e1-ac36-0002a5d5c51b')[0]

# Buffer initialization and n
buffer=[]
buffer_size=10000
for i in range (0,buffer_size):
    buffer.append([0,0,0,0,0])
n=0
i=0
data_verif=False

while True:
    if i%buffer_size==0 and i!=0:
        np.save(cwd +'/data/' + dt.datetime.now().strftime('%H:%M:%S.%f'), buffer)
        i=0
    val_unpacked=unpack('hhh', val_packed)
    buffer[i][0]=n
    buffer[i][1]=dt.datetime.now().strftime('%H:%M:%S.%f')
    buffer[i][2]=val_unpacked[0]
    buffer[i][3]=val_unpacked[1]
    buffer[i][4]=val_unpacked[2]
    n+=1
    i+=1
