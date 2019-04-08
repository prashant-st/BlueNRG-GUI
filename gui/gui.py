from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
from multiprocessing import Pool, Array, Process
from bluepy import btle
from struct import *
import sys
import matplotlib.animation as animation

macAdresses = ('F1:E5:A8:F0:96:80', 'E4:69:61:26:E6:23')
sensor_serive_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
acc_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
processes = [Process() for count in macAdresses]
data = Array('h', 12)

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

    def handleNotification(self, cHandle, data):         #Need to distinguish between pheripherals
        data_unpacked=unpack('hhhhhhIH', data)
        if self.address == 'F1:E5:A8:F0:96:80':
            self.dataarray[0] = data_unpacked[0]
            self.dataarray[1] = data_unpacked[1]
            self.dataarray[2] = data_unpacked[2]
            self.dataarray[3] = data_unpacked[3]
            self.dataarray[4] = data_unpacked[4]
            self.dataarray[5] = data_unpacked[5]
        print(self.dataarray)

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
    for idx, name in enumerate(macAdresses):
        process = Process(target=run_process, args=(macAdresses[idx], data))
        processes[idx] = process
        process.start()

def disconnectProcedure():
    for idx, name in enumerate(macAdresses):
        processes[idx].terminate()
    print("Devices disconnected")

def chooseSaveDirectory():
    print("Choose save directory...")

def animate(i, ys1, ys2, ys3):
    global data

    # Add y to list
    acc_x = data[0]
    acc_y = data[1]
    acc_z = data[2]

    ys1.append(acc_x)
    ys2.append(acc_y)
    ys3.append(acc_z)

    # Limit y list to set number of items
    ys1 = ys1[-x_len:]
    ys2 = ys2[-x_len:]
    ys3 = ys3[-x_len:]

    # Update line with new Y values
    line[0].set_ydata(ys1)
    line[1].set_ydata(ys2)
    line[2].set_ydata(ys3)

    return line

# Creating main frame
mainFrame = Frame(root, width=500, height=500)
mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# Buttons
connectButton = Button(mainFrame, text="CONNECT, SYNC AND START", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20)
connectButton.grid(row=0, column=0, padx=20, pady=100)
startButton = Button(mainFrame, text="DISCONNECT", bg="orange", fg="white", command=disconnectProcedure, padx=20, pady=20)
startButton.grid(row=1, column=0, padx=20, pady=5)
saveButton = Button(mainFrame, text="CHOOSE SAVE DIRECTORY", bg="orange", fg="white", command=chooseSaveDirectory, padx=20, pady=20)
saveButton.grid(row=2, column=0, padx=20, pady=100)

# Plot Initialization
# Parameters
x_len = 300         # Number of points to display
y_range = [-2000, 2000]  # Range of possible Y values to display
xs = list(range(0, x_len))
ys1 = [0] * x_len
ys2 = [0] * x_len
ys3 = [0] * x_len

f = Figure(figsize=(5, 5), dpi=100)
a = f.add_subplot(111)
# Create a blank line. We will update the line in animate
line1, = a.plot(xs, ys1)
line2, = a.plot(xs, ys2)
line3, = a.plot(xs, ys3)
line = [line1, line2, line3]
a.set_ylim(y_range)
a.set_title('Device 1 Data')
a.set_xlabel('Showing the last 300 samples')

canvas = FigureCanvasTkAgg(f, master=root)
canvas.draw()
canvas.get_tk_widget().grid(row=0, column=1, sticky=(N, W, E, S))



# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(f, animate, fargs=(ys1, ys2, ys3,), interval=50, blit=False)





while True:
    root.update_idletasks()
    root.update()


