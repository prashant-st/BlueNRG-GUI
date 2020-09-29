from multiprocessing import Value, Array

# Variables shared between files
macAdresses = []

# Constants
LOCATIONS = ["Left Arm","Right Arm", "Right Leg", "Left Leg", "Center"]

# Shared variables among processes
dataToDisplay = Array('h', 15)
masterClock = Value('I', 0)
identifyActivity = Value('i', 0)
