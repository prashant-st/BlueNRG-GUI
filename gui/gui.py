from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from bluepy import btle
from struct import *


BlueNRG_MAC = ["F1:E5:A8:F0:96:80", "E4:69:61:26:E6:23"]
sensor_service_UUID = '02366e80-cf3a-11e1-9ab4-0002a5d5c51b'
acc_UUID = '340a1b80-cf4b-11e1-ac36-0002a5d5c51b'


root = Tk()
root.title("Multimodal Seizure Detection")
# root.iconbitmap('snake.ico')
root.geometry("1000x600")
root.resizable(0, 0)

class BluetoothDevice:
    def __init__(self, adressmac):
        self.service = 0
        self.char = 0
        self.peripheral = btle.Peripheral(adressmac, btle.ADDR_TYPE_RANDOM)


class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        data_unpacked=unpack('hhhhhhIH', data)
        print(data_unpacked)

def connectProcedure():
    BlueNRG_devices = []
    for deviceNumber, macAdress in enumerate(BlueNRG_MAC):
        print("Connecting to BlueNRG -", deviceNumber+1, "...")
        BlueNRG = BluetoothDevice(BlueNRG_MAC[deviceNumber])
        BlueNRG_devices.append(BlueNRG)
        BlueNRG_devices[deviceNumber].peripheral.setMTU(200)
        BlueNRG_devices[deviceNumber].peripheral.setDelegate(MyDelegate())
        print("BlueNRG2 -", deviceNumber+1, " Services...")
        for svc in BlueNRG_devices[deviceNumber].peripheral.services:
            print(str(svc))
        print("BlueNRG2 -", deviceNumber+1, " Characteristics...")
        BlueNRG_devices[deviceNumber].service = BlueNRG_devices[deviceNumber].peripheral.getServiceByUUID(sensor_service_UUID)
        BlueNRG_devices[deviceNumber].char= BlueNRG_devices[deviceNumber].service.getCharacteristics(acc_UUID)[0]
    print("The connection procedure was successful")

def startProcedure():
    print("Starting...")


def chooseSaveDirectory():
    print("Choose save directory...")

# Creating main frame
mainFrame = Frame(root, width=500, height=500)
mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# Buttons
connectButton = Button(mainFrame, text="CONNECT", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20)
connectButton.grid(row=0, column=0, padx=20, pady=100)
startButton = Button(mainFrame, text="SYNC & START", bg="orange", fg="white", command=startProcedure, padx=20, pady=20)
startButton.grid(row=1, column=0, padx=20, pady=5)
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
