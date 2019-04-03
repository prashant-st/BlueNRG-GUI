from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


root = Tk()
root.title("CHUM's seizure detection application")


def connectProcedure():
    print("Connecting...")


def startProcedure():
    print("Starting...")


def chooseSaveDirectory():
    print("Choose save directory...")

# Creating main frame
mainFrame = Frame(root, width=500, height=500)
mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Buttons
connectButton = Button(mainFrame, text="CONNECT", bg="orange", fg="white", command=connectProcedure)
connectButton.grid(row=0, column=0, padx=5, pady=100)
startButton = Button(mainFrame, text="SYNC & START", bg="orange", fg="white", command=startProcedure)
startButton.grid(row=1, column=0, padx=5, pady=5)
saveButton = Button(mainFrame, text="CHOOSE SAVE DIRECTORY", bg="orange", fg="white", command=chooseSaveDirectory)
saveButton.grid(row=2, column=0, padx=5, pady=100)

# Plotting
f = Figure(figsize=(5, 5), dpi=100)
a = f.add_subplot(111)
a.plot([1, 2, 3, 4, 5, 6, 7, 8, 9], [5, 6, 1, 3, 8, 9, 3, 5, 4])
canvas = FigureCanvasTkAgg(f, master=root)
canvas.draw()
canvas.get_tk_widget().grid(row=0, column=1)


root.mainloop()
