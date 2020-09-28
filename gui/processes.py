from settings import *
import logging
import logging.handlers
import os
from multiprocessing import Array, Barrier
from bluepy import btle
import datetime as dt
import time
import random
import signal, psutil

# Constants
SENSOR_SERVICE_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
ACC_SERVICE_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
START_SERVICE_UUID = '2c41cc24-cf13-11e1-4fdf-0002a5d5c51b'

def runProcess(peripheral, barrier, queue):  
    # Logging configuration
    h = logging.handlers.QueueHandler(queue)  # Just the one handler needed
    logger = logging.getLogger()
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)
    
    while True:
        try:
            time.sleep((peripheral.index+1)*2.02 + random.random())
            # Connections
            print("Connecting to BlueNRG - " + peripheral.location + " Device...")

            BlueNRG = btle.Peripheral(peripheral.address, btle.ADDR_TYPE_RANDOM)
            BlueNRG.setDelegate(peripheral)

            # Service retrieval
            BlueNRGService = BlueNRG.getServiceByUUID(SENSOR_SERVICE_UUID)

            # Char
            BlueNRGAccChar = BlueNRGService.getCharacteristics(ACC_SERVICE_UUID)[0]
            BlueNRGStartChar = BlueNRGService.getCharacteristics(START_SERVICE_UUID)[0]

            print("Connection successfull for BlueNRG - " + peripheral.location + " Device...")

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
            print("A disconnection occured for BlueNRG - " + peripheral.location + " Device. Retrying...")
            time.sleep(1)

def runLogger(queue):
    # Configure logger
    logger = logging.getLogger()
    h = logging.handlers.WatchedFileHandler('logger.log', 'a')
    f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
    h.setFormatter(f)
    logger.addHandler(h)
    while True:
        try:
            record = queue.get()
            logger.handle(record)
        except Exception:
            import sys, traceback
            print('Error Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

def killAllProcesses():
    try:
      parent = psutil.Process(os.getpid())
    except psutil.NoSuchProcess:
      return
    children = parent.children(recursive=True)
    for process in children:
      process.send_signal(signal.SIGTERM)
