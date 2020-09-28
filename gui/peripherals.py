from tkinter import *
from tkinter import ttk
from settings import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os
from multiprocessing import Value, Array, Process, Lock, Barrier
from bluepy import btle
from struct import *
import sys
import matplotlib.animation as animation
import numpy as np
import datetime as dt
import time
import random
import signal, psutil

class MyDelegate(btle.DefaultDelegate):
    badConnectionTreshold = 500 
    
    def __init__(self, address, index, location):
        btle.DefaultDelegate.__init__(self)
        self.address = address
        self.index = index
        self.location = location
        self.badConnectionCounter = 0 
        self.saveFile = open("Output - " + str(location) + " - " + dt.datetime.now().strftime('%c') + ".txt", "a")

    def __del__(self):
        self.saveFile.close()
        
    def evaluateConnectionQuality(self):
        # Update counter if connection is bad
        if unsent[self.index] > 240:
            self.badConnectionCounter += 1
        else:
            self.badConnectionCounter = 0

        # Disconnect if connection has been bad for a while
        if(self.badConnectionCounter == self.badConnectionTreshold):
            print("Reconnecting to BlueNRG2-" + str(self.index + 1) + " because of too many missing paquets")
            raise btle.BTLEDisconnectError
    
    def saveData(self, dataUnpacked):
        self.saveFile.write(str(dataUnpacked + (seizure.value,)) + "\t" + dt.datetime.now().strftime('%m/%d/%Y, %H:%M:%S.%f') + "\n")
        self.saveFile.flush()
        


class ACM(MyDelegate):
    def __init__(self, address, index, location):
        MyDelegate.__init__(self, address, index, location)
        
    def handleNotification(self, cHandle, dataBLE):
        dataUnpacked=unpack('hhhhhhIH', dataBLE)
        
        # Device identification and allocation in the shared array
        # Depending on the device, different data will be displayed
        for i in range(3):
            dataToDisplay[i + self.index*3] = dataUnpacked[i]

        # Get the number of unsent samples on the peripheral side
        unsent[self.index] = dataUnpacked[7]
        
        # Update master clock
        if(dataUnpacked[6] > masterClock.value):
            masterClock.value = dataUnpacked[6]

        self.evaluateConnectionQuality()
                    
        self.saveData(dataUnpacked)

				
class ECG(MyDelegate):
    def __init__(self, address, index, location):
        MyDelegate.__init__(self, address, index, location)
        
    def handleNotification(self, cHandle, dataBLE):
        dataUnpacked=unpack('hhh', dataBLE[0:6]) + unpack('<i', dataBLE[6:9] + b'\x00') + unpack('<i', dataBLE[9:12] + b'\x00') + unpack('<i', dataBLE[12:15] + b'\x00') + unpack('I', dataBLE[15:19]) +  (dataBLE[19],)

        # Device identification and allocation in the shared array
        # Depending on the device, different data will be displayed
        dataToDisplay[self.index*3] = dataUnpacked[3]
        dataToDisplay[(self.index*3)+1] = dataUnpacked[4]

        # Get the number of unsent samples on the peripheral side
        unsent[self.index] = dataUnpacked[7]
        
        # Update master clock
        if(dataUnpacked[6] > masterClock.value):
            masterClock.value = dataUnpacked[6]

        self.evaluateConnectionQuality()

        self.saveData(dataUnpacked)
				
class PPG(MyDelegate):
    def __init__(self, address, index, location):
        MyDelegate.__init__(self, address, index, location)
    
    def handleNotification(self, cHandle, dataBLE):
        dataUnpacked=unpack('=hhhIIIH', dataBLE)
        
        # Device identification and allocation in the shared array
        # Depending on the device, different data will be displayed
        dataToDisplay[self.index*3] = dataUnpacked[3]
        dataToDisplay[(self.index*3)+1] = dataUnpacked[4]

        # Get the number of unsent samples on the peripheral side
        unsent[self.index] = dataUnpacked[6]
        
        # Update master clock
        if(dataUnpacked[5] > masterClock.value):
            masterClock.value = dataUnpacked[5]
        
        self.evaluateConnectionQuality()

        self.saveData(dataUnpacked)

