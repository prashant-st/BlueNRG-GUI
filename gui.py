from peripheral import *
from processes import *
from settings import *
from tkinter import *
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os
from multiprocessing import Process, Barrier, Queue
from bluepy import btle
import matplotlib.animation as animation
import datetime as dt

# Commands
def connectProcedure():
    connectButton.config(state="disabled")
    disconnectButton.config(state="normal")
    identifyActivityButton.config(state="normal")
    identifyDevicesButton.config(state="disabled")
    print("Connecting the devices...")
    # Create dir to save data
    cwd = os.getcwd()
    os.mkdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    os.chdir(cwd + "/Recordings - " + dt.datetime.now().strftime('%c'))
    # Create peripheral objects
    peripherals = [ACM(macAdresses[i], i, LOCATIONS[i]) for i in range(5) if macAdresses[i] != '']
    # Create barrier object
    barrier = Barrier(len(peripherals))
    # Configure and start logging processes
    queue = Queue(-1)
    process = Process(target=runLogger, args=(queue,))
    process.start()
    # Start processes
    for peripheral in peripherals:
        process = Process(target=runProcess, args=(peripheral, barrier, queue))
        process.start()
    
       
def disconnectProcedure():
    masterClock.value = 0
    connectButton.config(state="normal")
    disconnectButton.config(state="disabled")
    identifyActivityButton.config(state="disabled")
    identifyDevicesButton.config(state="normal")
    identifyActivityButton.configure(bg="orange")
    identifyActivity.value = 0
    os.chdir("..")
    killAllProcesses()
    print("Devices disconnected")

def closeProcedure():
    killAllProcesses()
    print("Application closed by user's request")
    root.destroy()

def identifyActivityProcedure():
    if identifyActivity.value == 0:
        identifyActivityButton.configure(bg="red")
        identifyActivity.value = 1
        print("Activity identification was added to the timestamps")
    else:
        identifyActivityButton.configure(bg="orange")
        identifyActivity.value = 0
        print("Activity identification was removed from the timestamps")

def identifyDevicesProcedure():
    global macAdresses
    connectButton.config(state="normal")
    disconnectButton.config(state="disabled")
    identifyActivityButton.config(state="disabled")
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

root = Tk()
root.title("Activity Recognition based on Movement Utility")
root.geometry("1000x600")
root.resizable(0, 0)
plt.style.use('ggplot')

# Creating main frame
mainFrame = Frame(root, width=500, height=500)
mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=0)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)
root.protocol('WM_DELETE_WINDOW', closeProcedure)

# Combobox
combo = ttk.Combobox(root, values = ["Device 1 - " + str(LOCATIONS[0]), "Device 2 - " + str(LOCATIONS[1]), "Device 3 - " + str(LOCATIONS[2]), "Device 4 - " + str(LOCATIONS[3]), "Device 5 - " + str(LOCATIONS[4])])
combo.grid(row=1, column=2, padx=10, pady=5)
combo.current(0)
combo.bind("<<ComboboxSelected>>", changeDevice)

# Buttons
identifyDevicesButton = Button(mainFrame, text="IDENTIFY DEVICES", bg="orange", fg="white", command=identifyDevicesProcedure, padx=20, pady=20)
identifyDevicesButton.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
connectButton = Button(mainFrame, text="CONNECT & START", bg="orange", fg="white", command=connectProcedure, padx=20, pady=20, state="disable")
connectButton.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
disconnectButton = Button(mainFrame, text="DISCONNECT", bg="orange", fg="white", command=disconnectProcedure, padx=20, pady=20, state="disable")
disconnectButton.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
identifyActivityButton = Button(mainFrame, text="IDENTIFY ACTIVITY", bg="orange", fg="white", command=identifyActivityProcedure, padx=20, pady=20, state="disable")
identifyActivityButton.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

# Entry
entries = []
for i in range(5):
    entry = Entry(mainFrame, font=40)
    entry.grid(row=i, column=1, padx=10, pady=1)
    entries.append(entry)
    

# Labels for entries
for i in range(5):
    label = Label(mainFrame, text="MAC Adress -" + " Device " + str(i+1) + " - " + str(LOCATIONS[i]))
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
line = [a.plot(xs, ys[i])[0] for i in range(3)]

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

