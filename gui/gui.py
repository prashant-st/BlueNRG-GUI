from tkinter import *
from tkinter import ttk
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

# Globals
macAdresses = []
locations = ["Left Arm (PPG)","Right Arm", "Right Leg", "Left Leg", "Center (ECG)"]

# Constants
SENSOR_SERVICE_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
ACC_SERVICE_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
START_SERVICE_UUID = '2c41cc24-cf13-11e1-4fdf-0002a5d5c51b'

# Shared variables among processes
dataToDisplay = Array('h', 15)
unsent = Array('H', 5)
masterClock = Value('I', 0)
seizure = Value('i', 0)

root = Tk()
root.title("Multimodal Seizure Detection Utility")
root.geometry("1000x600")
root.resizable(0, 0)
plt.style.use('ggplot')


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

def connectProcedure():
    connectButton.config(state="disabled")
    disconnectButton.config(state="normal")
    seizureButton.config(state="disabled")
    identifyDevicesButton.config(state="disabled")
    print("Connecting the devices...")
    # Create dir to save data
    cwd = os.getcwd()
    os.mkdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    os.chdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    # Create peripheral objects
    peripherals = []
    if macAdresses[0] != '':
        peripherals.append(PPG(macAdresses[0], 0, locations[0]),)
    if macAdresses[1] != '':
        peripherals.append(ACM(macAdresses[1], 1, locations[1]),)
    if macAdresses[2] != '':
        peripherals.append(ACM(macAdresses[2], 2, locations[2]),)
    if macAdresses[3] != '':
        peripherals.append(ACM(macAdresses[3], 3, locations[3]),)
    if macAdresses[4] != '':
        peripherals.append(ECG(macAdresses[4], 4, locations[4]),)
    # Create barrier object
    barrier = Barrier(len(peripherals))
    # Start processes
    for peripheral in peripherals:
        process = Process(target=runProcess, args=(peripheral, barrier))
        process.start()
    Process(target=runDebug).start()


def runDebug():
    # Create debug file
    debugfile = open("debug" + " - " + dt.datetime.now().strftime('%c') + ".txt", "a")
    while True:
        # Save debug data
        debugfile.write(str((unsent[0], unsent[1], unsent[2], unsent[3], unsent[4])) + "\n")
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
       
def disconnectProcedure():
    masterClock.value = 0
    connectButton.config(state="normal")
    disconnectButton.config(state="disabled")
    seizureButton.config(state="disabled")
    identifyDevicesButton.config(state="normal")
    seizureButton.configure(bg="orange")
    seizure.value = 0
    os.chdir("..")
    killAllProcesses()
    print("Devices disconnected")

def closeProcedure():
    killAllProcesses()
    print("Application closed by user's request")
    root.destroy()

def seizureSave():
    if seizure.value == 0:
        seizureButton.configure(bg="red")
        seizure.value = 1
        print("Seizure identification was added to the timestamps...")
    else:
        seizureButton.configure(bg="orange")
        seizure.value = 0
        print("Seizure identification was removed from the timestamps...")

def identifyDevices():
    global macAdresses
    connectButton.config(state="normal")
    disconnectButton.config(state="disabled")
    seizureButton.config(state="disabled")
    identifyDevicesButton.config(state="normal")
    macAdresses = [entries[i].get() for i in range(5)] 
    print("The devices' MAC adresses were changed and added")
    
def changeDevice(event):
    global line
    #Remove data from previous device
    for i in range(x_len):
        for idx in range(3):
            ys[idx].append(0)
            ys[idx] = ys[idx][-x_len:]
            line[idx].set_ydata(ys[idx])
    title = "Device " + str(combo.current()+1) + " data"
    a.set_title(title)


def animate(i, ys):
    deviceidx = combo.current() * 3
    for idx in range(3):
        ys[idx].append(dataToDisplay[idx + deviceidx])
        ys[idx] = ys[idx][-x_len:]
        line[idx].set_ydata(ys[idx])

    return line

# Creating main frame
mainFrame = Frame(root, width=500, height=500)
mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=0)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)
root.protocol('WM_DELETE_WINDOW', closeProcedure)

# Combobox
combo = ttk.Combobox(root, values = ["Device 1 - " + str(locations[0]), "Device 2 - " + str(locations[1]), "Device 3 - " + str(locations[2]), "Device 4 - " + str(locations[3]), "Device 5 - " + str(locations[4])])
combo.grid(row=1, column=2, padx=10, pady=5)
combo.current(0)
combo.bind("<<ComboboxSelected>>", changeDevice)

# Buttons
identifyDevicesButton = Button(mainFrame, text="IDENTIFY DEVICES", bg="orange", fg="white", command=identifyDevices, padx=20, pady=20)
identifyDevicesButton.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
connectButton = Button(mainFrame, text="CONNECT & START", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20, state="disable")
connectButton.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
disconnectButton = Button(mainFrame, text="DISCONNECT", bg="orange", fg="white", command=disconnectProcedure, padx=20, pady=20, state="disable")
disconnectButton.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
seizureButton = Button(mainFrame, text="IDENTIFY SEIZURE", bg="orange", fg="white", command=seizureSave, padx=20, pady=20, state="disable")
seizureButton.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

# Entry
entries = []
for i in range(5):
    entry = Entry(mainFrame, font=40)
    entry.grid(row=i, column=1, padx=10, pady=1)
    entries.append(entry)
    

# Labels for entries
for i in range(5):
    label = Label(mainFrame, text="Device " + str(i) + " - " + str(locations[i]))
    label.grid(row=i, column=0, padx=5)

# Plot Initialization
# Parameters
ys = []
x_len = 300         # Number of points to display
y_range = [-35000, 35000]  # Range of possible Y values to display
xs = list(range(0, x_len))
for i in range(3):
    ys.append([0] * x_len)

f = Figure(figsize=(5, 5), dpi=100)
a = f.add_subplot(111)
# Create a blank line. We will update the line in animate
line1, = a.plot(xs, ys[0])
line2, = a.plot(xs, ys[1])
line3, = a.plot(xs, ys[2])
line = [line1, line2, line3]

a.set_ylim(y_range)
a.set_title('Device 1 Data')
a.set_xlabel('Showing the last 300 samples')

canvas = FigureCanvasTkAgg(f, master=root)
canvas.draw()
canvas.get_tk_widget().grid(row=0, column=2, sticky=(N, W, E, S))

toolbarFrame = Frame(master=root)
toolbarFrame.grid(row=2, column=2, sticky=(W,E))
toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)
toolbar.update()

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(f, animate, fargs=(ys,), interval=20, blit=True)

while True:
    root.update_idletasks()
    root.update()

