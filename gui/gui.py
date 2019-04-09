from tkinter import *
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
from multiprocessing import Value, Array, Process
from bluepy import btle
from struct import *
import sys
import matplotlib.animation as animation
import numpy as np
import datetime as dt


macAdresses = ('F1:E5:A8:F0:96:80', 'E4:69:61:26:E6:23')
sensor_serive_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
acc_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
deviceidx = 0
processes = [Process() for count in macAdresses]
data = Array('h', 12)
seizure = Value('i', 0)

root = Tk()
root.title("Multimodal Seizure Detection Utility")
# root.iconbitmap('snake.ico')
root.geometry("1000x600")
root.resizable(0, 0)


class MyDelegate(btle.DefaultDelegate):
    def __init__(self, _address, _dataarray):
        btle.DefaultDelegate.__init__(self)
        self.address = _address
        self.dataarray = _dataarray
        # Open file to save later on
        self.save_file = open("Output - " + str(_address) + ".txt", "w")

    def __del__(self):
        self.save_file.close()

    def handleNotification(self, cHandle, data):
        data_unpacked=unpack('hhhhhhIH', data)
        # Device identification and allocation in the shared array
        if self.address == 'F1:E5:A8:F0:96:80':
            for i in range(3):
                self.dataarray[i] = data_unpacked[i]
        if self.address == 'E4:69:61:26:E6:23':
            for i in range(3):
                self.dataarray[i+3] = data_unpacked[i]
        # Save the data
        self.save_file.write(str(data_unpacked) + " " + str(seizure.value) + "\n")

def run_process(address, data):
    # Connections
    print("Connecting to BlueNRG2...")
    BlueNRG = btle.Peripheral(address, btle.ADDR_TYPE_RANDOM)
    BlueNRG.setDelegate(MyDelegate(address, data))
    print("BlueNRG2 Services...")
    for svc in BlueNRG.services:
        print(str(svc))

    # Service retrieval
    BlueNRG_service = BlueNRG.getServiceByUUID(sensor_serive_UUID)

    # Char
    print("BlueNRG2 Characteristics...")
    BlueNRG_1_acc_char = BlueNRG_service.getCharacteristics(acc_UUID)[0]

    # Setting the notifications on
    BlueNRG.writeCharacteristic(BlueNRG_1_acc_char.valHandle + 1, b'\x01\x00')

    while True:
        if BlueNRG.waitForNotifications(1.0):
            # handleNotification() was called
            continue

        print("Waiting...")

def connectProcedure():
    # Create shared memory
    global processes
    print("Connecting the devices, syncing and starting...")
    # Create dir to save data
    cwd = os.getcwd()
    os.mkdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    os.chdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    for idx, name in enumerate(macAdresses):
        process = Process(target=run_process, args=(macAdresses[idx], data))
        processes[idx] = process
        process.start()

def disconnectProcedure():
    os.chdir("..")
    try:
        for idx, name in enumerate(macAdresses):
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

def changeDevice(event):
    global deviceidx
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
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.protocol('WM_DELETE_WINDOW', closeProcedure)

# Combobox
combo = ttk.Combobox(root, values = ["Device 1", "Device 2"])
combo.grid(row=1, column=1, padx=20, pady=5)
combo.current(0)
combo.bind("<<ComboboxSelected>>", changeDevice)

# Buttons
connectButton = Button(mainFrame, text="CONNECT, SYNC AND START", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20)
connectButton.grid(row=0, column=0, padx=20, pady=100)
startButton = Button(mainFrame, text="DISCONNECT", bg="orange", fg="white", command=disconnectProcedure, padx=20, pady=20)
startButton.grid(row=1, column=0, padx=20, pady=5)
seizureButton = Button(mainFrame, text="IDENTIFY SEIZURE", bg="orange", fg="white", command=seizureSave, padx=20, pady=20)
seizureButton.grid(row=3, column=0, padx=20, pady=100)



# Plot Initialization
# Parameters
ys = []
x_len = 300         # Number of points to display
y_range = [-5000, 5000]  # Range of possible Y values to display
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
canvas.get_tk_widget().grid(row=0, column=1, sticky=(N, W, E, S))

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(f, animate, fargs=(ys,), interval=50, blit=False)

while True:
    root.update_idletasks()
    root.update()


