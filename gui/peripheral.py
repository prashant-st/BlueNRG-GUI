from bluepy import btle
from struct import *
import binascii
import datetime as dt
import sys
import ctypes as ct
import time

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        data_unpacked=unpack('hhhhhhIH', data)
        print(data_unpacked);
            
BlueNRG_1_MAC = str(sys.argv[1])



sensor_serive_UUID='02366e80-cf3a-11e1-9ab4-0002a5d5c51b'

acc_UUID='340a1b80-cf4b-11e1-ac36-0002a5d5c51b'


# Connections
print ("Connecting to BlueNRG2-1...")
BlueNRG_1 = btle.Peripheral(BlueNRG_1_MAC, btle.ADDR_TYPE_RANDOM)
BlueNRG_1.setDelegate( MyDelegate() )
print ("BlueNRG2-1 Services...")
for svc in BlueNRG_1.services:
    print (str(svc))

#Service retrieval
BlueNRG_1_service=BlueNRG_1.getServiceByUUID(sensor_serive_UUID)

#Char retriveal
print ("BlueNRG2-1 Characteristics...")
BlueNRG_1_acc_char=BlueNRG_1_service.getCharacteristics(acc_UUID)[0]


#Setting the notifications on
BlueNRG_1.writeCharacteristic(BlueNRG_1_acc_char.valHandle+1, b'\x01\x00')


while True:
    if BlueNRG_1.waitForNotifications(1.0) :
        # handleNotification() was called
        continue

    print("Waiting...")

