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


macAdresses = ['00:00:00:00:00:00','00:00:00:00:00:00','00:00:00:00:00:00','00:00:00:00:00:00', '00:00:00:00:00:00']
locations = ["Right Arm (PPG)","Left Arm", "Right Leg", "Left Leg", "Center (ECG)"]
sensor_serive_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
acc_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
start_UUID = '2c41cc24-cf13-11e1-4fdf-0002a5d5c51b'
deviceidx = 0
processes = [Process() for count in macAdresses]
data = Array('h', 15)
seizure = Value('i', 0)
startNotify = Value('i', 0)
syncRequest = Value('i', 0)
numberofdevices = 0


root = Tk()
root.title("Multimodal Seizure Detection Utility")
# root.iconbitmap('snake.ico')
root.geometry("1000x600")
root.resizable(0, 0)
plt.style.use('ggplot')


class MyDelegate(btle.DefaultDelegate):
    def __init__(self, _address, _index, _location):
        btle.DefaultDelegate.__init__(self)
        self.address = _address
        self.index = _index
        self.location = _location
        self.sampleNumber = 0
        self.lastsavedData = tuple()
        if self.location == "Center (ECG)":
            self.syncInterval = 1250
        else:
            self.syncInterval = 1000
        # Open file to save later on     
        self.save_file = open("Output - " + str(self.location) +".txt", "w")


    def __del__(self):
        self.save_file.close()

    def handlesyncRequest(self):
        print("Entering handlesyncRequest... " + self.address + " Missing " + str(self.syncInterval-self.sampleNumber))
        while self.sampleNumber != self.syncInterval:
            tempTuple = (seizure.value,)
            self.save_file.write(str(self.lastsavedData + tempTuple) + "\t" + "This sample was copied" +  dt.datetime.now().strftime('%m/%d/%Y, %H:%M:%S.%f') + "\n")
            self.sampleNumber = self.sampleNumber + 1
        self.save_file.flush()
        print(self.address + " is ready")
        #Reset counter
        self.sampleNumber = 0

class ACM(MyDelegate):
    def handleNotification(self, cHandle, data_BLE):
        global data
        if syncRequest.value == 0:
            data_unpacked=unpack('hhhhhhIH', data_BLE)
            # Verify that this is new data and not leftover values from the SPTBLE-1S FIFO
            if not((self.sampleNumber < self.syncInterval/30) and (data_unpacked[6] > 2 * self.syncInterval)):
                # Device identification and allocation in the shared array
                # Depending on the device, different data will be displayed
                for i in range(3):
                    data[i + self.index*3] = data_unpacked[i]
                    
                # Save latest sample for further processing
                self.lastsavedData = data_unpacked

                # Save the data
                tempTuple = (seizure.value,)
                self.save_file.write(str(data_unpacked + tempTuple) + "\t" + dt.datetime.now().strftime('%m/%d/%Y, %H:%M:%S.%f') + "\n")
                self.save_file.flush()

                # Increment sample counter
                self.sampleNumber = self.sampleNumber + 1

                # Raise flag if one of the peripherals reaches syncInterval first
                if self.sampleNumber == self.syncInterval:
                    syncRequest.value = 1

                #print("Processing " + str(self.sampleNumber) + " for " + str(self.address))
				
class ECG(MyDelegate):
    def handleNotification(self, cHandle, data_BLE):
        global data
        
        if syncRequest.value == 0:
            data_unpacked=unpack('hhhhiiHH', data_BLE)
            # Verify that this is new data and not leftover values from the SPTBLE-1S FIFO
            if not((self.sampleNumber < self.syncInterval/30) and (data_unpacked[6] > 2 * self.syncInterval)):
                # Device identification and allocation in the shared array
                # Depending on the device, different data will be displayed
                data[self.index*3] = data_unpacked[3]
                data[(self.index*3)+1] = data_unpacked[4]

                # Save latest sample for further processing
                self.lastsavedData = data_unpacked

                # Save the data
                tempTuple = (seizure.value,)
                self.save_file.write(str(data_unpacked + tempTuple) + "\t" + dt.datetime.now().strftime('%m/%d/%Y, %H:%M:%S.%f') + "\n")
                self.save_file.flush()

                # Increment sample counter
                self.sampleNumber = self.sampleNumber + 1

                # Raise flag if one of the peripherals reaches syncInterval first
                if self.sampleNumber == self.syncInterval:
                    syncRequest.value = 1

                #print("Processing " + str(self.sampleNumber) + " for " + str(self.address))
				
class PPG(MyDelegate):
    def handleNotification(self, cHandle, data_BLE):
        global data
        
        if syncRequest.value == 0:
            data_unpacked=unpack('=hhhIIIH', data_BLE)
            # Verify that this is new data and not leftover values from the SPTBLE-1S FIFO
            if not((self.sampleNumber < self.syncInterval/30) and (data_unpacked[5] > 2 * self.syncInterval)):
                # Device identification and allocation in the shared array
                # Depending on the device, different data will be displayed
                data[self.index*3] = data_unpacked[3]
                data[(self.index*3)+1] = data_unpacked[4]

                # Save latest sample for further processing
                self.lastsavedData = data_unpacked

                # Save the data
                tempTuple = (seizure.value,)
                self.save_file.write(str(data_unpacked + tempTuple) + "\t" + dt.datetime.now().strftime('%m/%d/%Y, %H:%M:%S.%f') + "\n")
                self.save_file.flush()

                # Increment sample counter
                self.sampleNumber = self.sampleNumber + 1

                # Raise flag if one of the peripherals reaches syncInterval first
                if self.sampleNumber == self.syncInterval:
                    syncRequest.value = 1

                #print("Processing " + str(self.sampleNumber) + " for " + str(self.address))

def run_process(address, index, location, lock, barrier):
    # Connections
    print("Connecting to BlueNRG2...")
    BlueNRG = btle.Peripheral(address, btle.ADDR_TYPE_RANDOM)
    if location == "Right Arm (PPG)":
        peripheral = PPG(address, index, location)
    elif location == "Center (ECG)":
        peripheral = ECG(address, index, location)
    else:
        peripheral = ACM(address, index, location)
    BlueNRG.setDelegate(peripheral)
    print("BlueNRG2 Services...")
    for svc in BlueNRG.services:
        print(str(svc))

    # Service retrieval
    BlueNRG_service = BlueNRG.getServiceByUUID(sensor_serive_UUID)

    # Char
    print("BlueNRG2 Characteristics...")
    BlueNRG_1_acc_char = BlueNRG_service.getCharacteristics(acc_UUID)[0]
    BlueNRG_1_start_char = BlueNRG_service.getCharacteristics(start_UUID)[0]

    # Waiting to start
    while startNotify.value!=1:
        continue
        
    # Setting the notifications on
    BlueNRG.writeCharacteristic(BlueNRG_1_acc_char.valHandle + 1, b'\x01\x00')

    while True:
        if syncRequest.value == 0:
            BlueNRG.waitForNotifications(1.0)
        else:
            peripheral.handlesyncRequest()
            # Wait until all process are ready to reset
            print(peripheral.address + " is waiting for sync")
            barrier.wait()
            BlueNRG.writeCharacteristic(BlueNRG_1_start_char.valHandle, b'\x01')
            print("Sync executed for " + peripheral.address)
            lock.acquire()
            syncRequest.value = 0
            lock.release()


def connectProcedure():
    global numberofdevices
    connectButton.config(state="disabled")
    disconnectButton.config(state="normal")
    seizureButton.config(state="disabled")
    startButton.config(state="normal")
    identifyDevicesButton.config(state="disabled")
    lock = Lock()
    barrier = Barrier(numberofdevices)
    # Create shared memory
    global processes
    print("Connecting the devices...")
    # Create dir to save data
    cwd = os.getcwd()
    os.mkdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    os.chdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    syncRequest = 0
    for idx, name in enumerate(macAdresses):
        if not(macAdresses[idx]==''):
            process = Process(target=run_process, args=(macAdresses[idx], idx, locations[idx], lock, barrier))
            processes[idx] = process
            process.start()
            time.sleep(2)
def startProcedure():
    global startNotify
    startNotify.value=1
    connectButton.config(state="disabled")
    disconnectButton.config(state="normal")
    seizureButton.config(state="normal")
    startButton.config(state="disabled")
    identifyDevicesButton.config(state="disabled")
    print("Recording started...")
       
def disconnectProcedure():
    global startNotify
    startNotify.value=0
    connectButton.config(state="normal")
    disconnectButton.config(state="disabled")
    seizureButton.config(state="disabled")
    identifyDevicesButton.config(state="normal")
    startButton.config(state="disabled")
    seizureButton.configure(bg="orange")
    seizure.value = 0
    os.chdir("..")
   
    for idx, name in enumerate(macAdresses):
        try:
            processes[idx].terminate()
        except AttributeError:
            pass
    print("Devices disconnected")

def closeProcedure():
    try:
        for idx, name in enumerate(macAdresses):
            processes[idx].terminate()
    except AttributeError:
        pass
    print("Application closed by user's request")
    root.destroy()

def seizureSave():
    global seizure
    if seizure.value == 0:
        seizureButton.configure(bg="red")
        seizure.value = 1
        print("Seizure identification was added to the timestamps...")
    else:
        seizureButton.configure(bg="orange")
        seizure.value = 0
        print("Seizure identification was removed from the timestamps...")

def identifyDevices(entry1, entry2, entry3, entry4, entry5):
    global numberofdevices
    connectButton.config(state="normal")
    disconnectButton.config(state="disabled")
    seizureButton.config(state="disabled")
    identifyDevicesButton.config(state="normal")
    macAdresses[0] = entry1
    macAdresses[1] = entry2
    macAdresses[2] = entry3
    macAdresses[3] = entry4
    macAdresses[4] = entry5
    for idx, name in enumerate(macAdresses):
        if not (macAdresses[idx]==''):
            numberofdevices = numberofdevices +1
    print("The devices' MAC adresses were changed and added")
    
def changeDevice(event):
    global deviceidx
    global line
    #Remove data from previous device
    for i in range(x_len):
        for idx in range(3):
            ys[idx].append(0)
            ys[idx] = ys[idx][-x_len:]
            line[idx].set_ydata(ys[idx])
            
    deviceidx = combo.current() * 3
    
    title = "Device " + str(combo.current()+1) + " Data"
    a.set_title(title)


def animate(i, ys):
    global data
    global deviceidx

    for idx in range(3):
        ys[idx].append(data[idx + deviceidx])
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
identifyDevicesButton = Button(mainFrame, text="IDENTIFY DEVICES", bg="orange", fg="white", command=lambda: identifyDevices(entry_RA.get(), entry_LA.get(), entry_RL.get(), entry_LL.get(), entry_C.get()), padx=20, pady=20)
identifyDevicesButton.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
connectButton = Button(mainFrame, text="CONNECT", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20, state="disable")
connectButton.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
startButton = Button(mainFrame, text="SYNC AND START", bg="orange", fg="white", command=startProcedure, padx=20, pady=20, state="disable")
startButton.grid(row=7, column=0, columnspan=2, padx=10, pady=10)
disconnectButton = Button(mainFrame, text="DISCONNECT", bg="orange", fg="white", command=disconnectProcedure, padx=20, pady=20, state="disable")
disconnectButton.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
seizureButton = Button(mainFrame, text="IDENTIFY SEIZURE", bg="orange", fg="white", command=seizureSave, padx=20, pady=20, state="disable")
seizureButton.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    
#Entry
entry_RA = Entry(mainFrame, font=40)
entry_RA.grid(row=0, column=1, padx=10, pady=1)
entry_LA = Entry(mainFrame, font=40)
entry_LA.grid(row=1, column=1, padx=10, pady=1)
entry_RL = Entry(mainFrame, font=40)
entry_RL.grid(row=2, column=1, padx=10, pady=1)
entry_LL = Entry(mainFrame, font=40)
entry_LL.grid(row=3, column=1, padx=10, pady=1)
entry_C = Entry(mainFrame, font=40)
entry_C.grid(row=4, column=1, padx=10, pady=1)

#Labels for entries
label_RA = Label(mainFrame, text="Device 1 - " + str(locations[0])).grid(row=0, column=0, padx=5)
label_LA = Label(mainFrame, text="Device 2 - " + str(locations[1])).grid(row=1, column=0, padx=5)
label_RL = Label(mainFrame, text="Device 3 - " + str(locations[2])).grid(row=2, column=0, padx=5)
label_LL = Label(mainFrame, text="Device 4 - " + str(locations[3])).grid(row=3, column=0, padx=5)
label_C = Label(mainFrame, text="Device 5 - " + str(locations[4])).grid(row=4, column=0, padx=5)

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


