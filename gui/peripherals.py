from settings import *
import logging
import logging.handlers
from bluepy import btle
from struct import *
import datetime as dt

class MyDelegate(btle.DefaultDelegate):
    badConnectionTreshold = 500 
    
    def __init__(self, address, index, location):
        btle.DefaultDelegate.__init__(self)
        self.address = address
        self.index = index
        self.location = location
        self.badConnectionCounter = 0 
        self.saveFile = open("Output - " + str(location) + " - " + dt.datetime.now().strftime('%c') + ".txt", "a")

    def __del__(self):
        self.saveFile.close()
        
    def evaluateConnectionQuality(self, unsent):
        logger = logging.getLogger()
        # Update counter if connection is bad
        if unsent > 10:
            if self.badConnectionCounter == 0:
                logger.log(logging.WARNING, "Connection is bad for BlueNRG - " + self.location + " Device")
            self.badConnectionCounter += 1
        else:
            if self.badConnectionCounter != 0:
                logger.log(logging.WARNING, "Connection is recovered for BlueNRG - " + self.location + " Device")
            self.badConnectionCounter = 0

        # Disconnect if connection has been bad for a while
        if(self.badConnectionCounter == self.badConnectionTreshold):
            logger.log(logging.ERROR, "Reconnecting to BlueNRG - " + self.location + " Device because of too many missing paquets")
            raise btle.BTLEDisconnectError
    
    def saveData(self, dataUnpacked):
        self.saveFile.write(str(dataUnpacked + (seizure.value,)) + "\t" + dt.datetime.now().strftime('%m/%d/%Y, %H:%M:%S.%f') + "\n")
        self.saveFile.flush()
        


class ACM(MyDelegate):
    def __init__(self, address, index, location):
        MyDelegate.__init__(self, address, index, location)
        
    def handleNotification(self, cHandle, dataBLE):
        dataUnpacked=unpack('hhhhhhIH', dataBLE)
        
        # Device identification and allocation in the shared array
        # Depending on the device, different data will be displayed
        for i in range(3):
            dataToDisplay[i + self.index*3] = dataUnpacked[i]
        
        # Update master clock
        if(dataUnpacked[6] > masterClock.value):
            masterClock.value = dataUnpacked[6]

        self.evaluateConnectionQuality(dataUnpacked[7])
                    
        self.saveData(dataUnpacked)

				
class ECG(MyDelegate):
    def __init__(self, address, index, location):
        MyDelegate.__init__(self, address, index, location)
        
    def handleNotification(self, cHandle, dataBLE):
        dataUnpacked=unpack('hhh', dataBLE[0:6]) + unpack('<i', dataBLE[6:9] + b'\x00') + unpack('<i', dataBLE[9:12] + b'\x00') + unpack('<i', dataBLE[12:15] + b'\x00') + unpack('I', dataBLE[15:19]) +  (dataBLE[19],)

        # Device identification and allocation in the shared array
        # Depending on the device, different data will be displayed
        dataToDisplay[self.index*3] = dataUnpacked[3]
        dataToDisplay[(self.index*3)+1] = dataUnpacked[4]
        
        # Update master clock
        if(dataUnpacked[6] > masterClock.value):
            masterClock.value = dataUnpacked[6]

        self.evaluateConnectionQuality(dataUnpacked[7])

        self.saveData(dataUnpacked)
				
class PPG(MyDelegate):
    def __init__(self, address, index, location):
        MyDelegate.__init__(self, address, index, location)
    
    def handleNotification(self, cHandle, dataBLE):
        dataUnpacked=unpack('=hhhIIIH', dataBLE)
        
        # Device identification and allocation in the shared array
        # Depending on the device, different data will be displayed
        dataToDisplay[self.index*3] = dataUnpacked[3]
        dataToDisplay[(self.index*3)+1] = dataUnpacked[4]
        
        # Update master clock
        if(dataUnpacked[5] > masterClock.value):
            masterClock.value = dataUnpacked[5]
        
        self.evaluateConnectionQuality(dataUnpacked[6])

        self.saveData(dataUnpacked)
