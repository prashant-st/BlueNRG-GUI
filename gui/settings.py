from multiprocessing import Value, Array

# Variables shared between files
macAdresses = []

# Constants
LOCATIONS = ["Left Arm (PPG)","Right Arm", "Right Leg", "Left Leg", "Center (ECG)"]

# Shared variables among processes
dataToDisplay = Array('h', 15)
unsent = Array('H', 5)
masterClock = Value('I', 0)
seizure = Value('i', 0)
