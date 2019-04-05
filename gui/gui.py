from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
from multiprocessing import Pool

BlueNRG_devices = []
connected=False

macAdresses=('F1:E5:A8:F0:96:80', 'E4:69:61:26:E6:23')

root = Tk()
root.title("Multimodal Seizure Detection Utility")
# root.iconbitmap('snake.ico')
root.geometry("1000x600")
root.resizable(0, 0)

def run_process(adress):
    os.system('python peripheral.py {}'.format(adress))

def connectProcedure():
    print("Connecting the devices, syncing and starting...")
    pool = Pool()
    pool.map(run_process, macAdresses)
    pool.close()
    pool.join()

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


