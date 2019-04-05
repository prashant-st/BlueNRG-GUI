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

macAdresses = ('F1:E5:A8:F0:96:80', 'E4:69:61:26:E6:23')
sensor_serive_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
acc_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
process = []

root = Tk()
root.title("Multimodal Seizure Detection Utility")
# root.iconbitmap('snake.ico')
root.geometry("1000x600")
root.resizable(0, 0)

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        data_unpacked=unpack('hhhhhhIH', data)
        print(data_unpacked);

def run_process(adress, data):
    # Connections
    print("Connecting to BlueNRG2...")
    BlueNRG = btle.Peripheral(adress, btle.ADDR_TYPE_RANDOM)
    BlueNRG.setDelegate(MyDelegate())
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
    global process
    data = Array('h', 12)
    print("Connecting the devices, syncing and starting...")
    for idx, name in enumerate(macAdresses):
        process.append(Process(target=run_process, args=(macAdresses[idx], data)))
    for idx, name in enumerate(macAdresses):
        process[idx].start()
    for idx, name in enumerate(macAdresses):
        process[idx].join()

def chooseSaveDirectory():
    print("Choose save directory...")

# Creating main frame
mainFrame = Frame(root, width=500, height=500)
mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# Buttons
connectButton = Button(mainFrame, text="CONNECT, SYNC AND START", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20)
connectButton.grid(row=0, column=0, padx=20, pady=100)
saveButton = Button(mainFrame, text="CHOOSE SAVE DIRECTORY", bg="orange", fg="white", command=chooseSaveDirectory, padx=20, pady=20)
saveButton.grid(row=2, column=0, padx=20, pady=100)

# Plot Initialization
f = Figure(figsize=(5, 5), dpi=100)
a = f.add_subplot(111)
a.plot([0], [0])
canvas = FigureCanvasTkAgg(f, master=root)
canvas.draw()
canvas.get_tk_widget().grid(row=0, column=1, sticky=(N, W, E, S))

root.mainloop()


