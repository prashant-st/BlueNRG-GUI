from bluepy import btle
from struct import *
import binascii
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import ctypes as ct
import time

bytes_sets=[[i*j for j in range (18)] for i in range(10)]
sets=[[i*j for j in range (8)] for i in range(10)]
class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        data_unpacked=unpack('hhhhhhIH', data)
#        for i in range(0,10):
#            for j in range (0,18):
#                bytes_sets[i][j]=data_unpacked[j+18*i]
#        for i in range(0,10):
#            sets[i][0]=ct.c_short(bytes_sets[i][0] + bytes_sets[i][1]*256)
#            sets[i][1]=ct.c_short(bytes_sets[i][2] + bytes_sets[i][3]*256)
#            sets[i][2]=ct.c_short(bytes_sets[i][4] + bytes_sets[i][5]*256)
#            sets[i][3]=ct.c_short(bytes_sets[i][6] + bytes_sets[i][7]*256)
#            sets[i][4]=ct.c_short(bytes_sets[i][8] + bytes_sets[i][9]*256)
#            sets[i][5]=ct.c_short(bytes_sets[i][10] + bytes_sets[i][11]*256)
#            sets[i][6]=ct.c_uint(bytes_sets[i][12]*256 + bytes_sets[i][13]*65536+ bytes_sets[i][15])
#            sets[i][7]=ct.c_ushort(bytes_sets[i][16] + bytes_sets[i][17]*256)
#        for i in sets:
#            print(i)
        print(data_unpacked);
            
BlueNRG_1_MAC="F1:E5:A8:F0:96:80"
BlueNRG_2_MAC="D1:D3:22:72:05:69"

sensor_serive_UUID='02366e80-cf3a-11e1-9ab4-0002a5d5c51b'

acc_UUID='340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
start_UUID='2c41cc24-cf13-11e1-4fdf-0002a5d5c51b'

# Connections
print ("Connecting to BlueNRG2-1...")
BlueNRG_1 = btle.Peripheral(BlueNRG_1_MAC, btle.ADDR_TYPE_RANDOM)
BlueNRG_1.setMTU(200);
BlueNRG_1.setDelegate( MyDelegate() )
print ("BlueNRG2-1 Services...")
for svc in BlueNRG_1.services:
    print (str(svc))

#print ("Connecting to BlueNRG2-2...")
#BlueNRG_2 = btle.Peripheral(BlueNRG_2_MAC, btle.ADDR_TYPE_RANDOM)
#BlueNRG_2.setDelegate( MyDelegate() )
#print ("BlueNRG2-2 Services...")
#for svc in BlueNRG_2.services:
#    print (str(svc))

#Service retrieval
BlueNRG_1_service=BlueNRG_1.getServiceByUUID(sensor_serive_UUID)
#BlueNRG_2_service=BlueNRG_2.getServiceByUUID(sensor_serive_UUID)

#Char retriveal
print ("BlueNRG2-1 Characteristics...")
BlueNRG_1_acc_char=BlueNRG_1_service.getCharacteristics(acc_UUID)[0]
BlueNRG_1_start_char=BlueNRG_1_service.getCharacteristics(start_UUID)[0]
#BlueNRG_1_gyr_char=BlueNRG_1_service.getCharacteristics(gyr_UUID)[0]

#print ("BlueNRG2-2 Characteristics...")
#BlueNRG_2_acc_char=BlueNRG_2_service.getCharacteristics(acc_UUID)[0]
#BlueNRG_2_gyr_char=BlueNRG_2_service.getCharacteristics(gyr_UUID)[0]

#Setting the notifications on
BlueNRG_1.writeCharacteristic(BlueNRG_1_acc_char.valHandle+1, b'\x01\x00')
BlueNRG_1.writeCharacteristic(BlueNRG_1_start_char.valHandle, b'\x31')
#BlueNRG_1.writeCharacteristic(BlueNRG_1_gyr_char.valHandle+1, b'\x01\x00')
#BlueNRG_2.writeCharacteristic(BlueNRG_2_acc_char.valHandle+1, b'\x01\x00')
#BlueNRG_2.writeCharacteristic(BlueNRG_2_gyr_char.valHandle+1, b'\x01\x00')

while True:
    if BlueNRG_1.waitForNotifications(1.0) :
        # handleNotification() was called
        continue

    print("Waiting...")

