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

# Constants
SENSOR_SERVICE_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
ACC_SERVICE_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
START_SERVICE_UUID = '2c41cc24-cf13-11e1-4fdf-0002a5d5c51b'

def runProcess(peripheral, barrier):  
    while True:
        try:
            time.sleep((peripheral.index+1)*2.02 + random.random())
            # Connections
            print("Connecting to BlueNRG2-" + str(peripheral.index + 1) + " ...")

            BlueNRG = btle.Peripheral(peripheral.address, btle.ADDR_TYPE_RANDOM)
            BlueNRG.setDelegate(peripheral)

            # Service retrieval
            BlueNRGService = BlueNRG.getServiceByUUID(SENSOR_SERVICE_UUID)

            # Char
            # print("BlueNRG2 Characteristics...")
            BlueNRGAccChar = BlueNRGService.getCharacteristics(ACC_SERVICE_UUID)[0]
            BlueNRGStartChar = BlueNRGService.getCharacteristics(START_SERVICE_UUID)[0]

            print("Connection successfull for BlueNRG2-" + str(peripheral.index + 1) + " ...")

            # Wait for connection update
            time.sleep(5)

            # Waiting to start (only for the initial sync)
            barrier.wait()
            barrier = Barrier(1)
            
            # Set timer to the right value
            BlueNRG.writeCharacteristic(BlueNRGStartChar.valHandle, (masterClock.value+40).to_bytes(4, byteorder='little'))
            
            # Setting the notifications on
            BlueNRG.writeCharacteristic(BlueNRGAccChar.valHandle + 1, b'\x01\x00')

            while True:
                BlueNRG.waitForNotifications(1.0)

        except btle.BTLEDisconnectError:
            print("A disconnection occured for BlueNRG2-" + str(peripheral.index + 1)+ " retrying...")
            # BlueNRG.disconnect()
            time.sleep(1)

def runDebug():
    # Create debug file
    debugfile = open("debug" + " - " + dt.datetime.now().strftime('%c') + ".txt", "a")
    while True:
        # Save debug data
        debugfile.write(str((*unsent,)) + "\n")
        debugfile.flush()
        time.sleep(0.1)

def killAllProcesses():
    try:
      parent = psutil.Process(os.getpid())
    except psutil.NoSuchProcess:
      return
    children = parent.children(recursive=True)
    for process in children:
      process.send_signal(signal.SIGTERM)
