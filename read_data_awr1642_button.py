import traceback
import serial
import serial.tools.list_ports
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from getch import getch #Getch = getChar, does single-char input.
from readchar import readkey, key

# Change the configuration file name
configFileName = 'AWR1642_SDK3.5.cfg'

CLIport = {}
Dataport = {}
byteBuffer = np.zeros(2**15,dtype = 'uint8')
byteBufferLength = 0;
if_button_is_pushed = 0


# ------------------------------------------------------------------

# Function to find ports for both CLIport and Dataport respectively
def findPorts(): 
    print('Looking for ports...', end='')
    pattern = "XDS110"
    ports = []
    for port in serial.tools.list_ports.comports():
        if pattern in str(port):
            ports.append(str(port).split()[0])
    ports.sort()

    if len(ports) < 2: 
        print("Ports not founds")
        return 
    
    if len(ports) > 2:
        print("Found ports")
        ports = ports[:2]

    ports1 = ports[0]
    ports2 = ports[1]
    print(f"-----port1(cliport):{ports1}, ----port2(dataport):{ports2}------")

    return ports1, ports2 

# ------------------------------------------------------------------

# Function to configure the serial ports and send the data from
# the configuration file to the radar
def serialConfig(configFileName):
    
    global CLIport
    global Dataport

    # Open the serial ports for the configuration and the data ports
    ports1, ports2 = findPorts()

    # Raspberry pi
    CLIport = serial.Serial(ports1, 115200)
    Dataport = serial.Serial(ports2, 921600)
    
    # Windows
    #CLIport = serial.Serial('COM4', 115200)
    #Dataport = serial.Serial('COM3', 921600)

    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        CLIport.write((i+'\n').encode())
        print(i)
        time.sleep(0.01)
        
    return CLIport, Dataport

# ------------------------------------------------------------------

# Function to parse the data inside the configuration file
def parseConfigFile(configFileName):
    configParameters = {} # Initialize an empty dictionary to store the configuration parameters
    
    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        
        # Split the line
        splitWords = i.split(" ")
        
        # Hard code the number of antennas, change if other configuration is used
        numRxAnt = 4
        numTxAnt = 2
        
        # Get the information about the profile configuration
        if "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1;
            
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2;
                
            digOutSampleRate = int(splitWords[11]);
            
        # Get the information about the frame configuration    
        elif "frameCfg" in splitWords[0]:
            
            chirpStartIdx = int(splitWords[1]);
            chirpEndIdx = int(splitWords[2]);
            numLoops = int(splitWords[3]);
            numFrames = int(splitWords[4]);
            framePeriodicity = float(splitWords[5]);

            
    # Combine the read data to obtain the configuration parameters           
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["dopplerResolutionMps"] = 3e8 / (2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
    configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)
    
    return configParameters
   
# ------------------------------------------------------------------

# Funtion to read and parse the incoming data
def readAndParseData18xx(Dataport, configParameters):
    global byteBuffer, byteBufferLength, hb100_data, slope, GestureNumber
    slope = 0  # detect falling slope for button
    GestureNumber = 1  # save with asceding order 'gesture1', 'gesture2' etc
    byteBuffer = np.zeros(2 ** 15, dtype='uint8')
    byteBufferLength = 0;
    # Constants
    # OBJ_STRUCT_SIZE_BYTES = 12;
    # BYTE_VEC_ACC_MAX_SIZE = 2**15;
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1;
    # MMWDEMO_UART_MSG_RANGE_PROFILE   = 2;

    maxBufferSize = 2**15;
    tlvHeaderLengthInBytes = 8;
    pointLengthInBytes = 16;
    magicWord = [2, 1, 4, 3, 6, 5, 8, 7]
    
    # Initialize variables
    magicOK = 0 # Checks if magic number has been read
    dataOK = 0 # Checks if the data has been read correctly
    # frameNumber = 0
    detObj = {}
    tlv_type = 0
    
     # Arrays to store gesture data for ML
    dtype = [('framenumber', np.int16), ('objnumber', np.int16), ('Range', np.float64),
             ('velocity', np.float64), ('peakval', np.float64), ('x', np.float64), ('y', np.float64)]

    global GestureData, FrameIndex  
    GestureData = np.array([(0, 0, 0, 0, 0, 0, 0)], dtype=dtype)
    FrameIndex = 1

    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype = 'uint8')
    byteCount = len(byteVec)
    print(readBuffer)

    # while(True):
    #     print("Helllo.....")
    
    # Check that the buffer is not full, and then add the data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength:byteBufferLength + byteCount] = byteVec[:byteCount]
        byteBufferLength = byteBufferLength + byteCount
        
    # Check that the buffer has some data
    if byteBufferLength > 16:
        
        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == magicWord[0])[0]

        # Confirm that is the beginning of the magic word and store the index in startIdx
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc:loc+8]
            if np.all(check == magicWord):
                startIdx.append(loc)
               
        # Check that startIdx is not empty
        if startIdx:
            print(startIdx)
            
            # Remove the data before the first start index
            if startIdx[0] > 0 and startIdx[0] < byteBufferLength:
                byteBuffer[:byteBufferLength-startIdx[0]] = byteBuffer[startIdx[0]:byteBufferLength]
                byteBuffer[byteBufferLength-startIdx[0]:] = np.zeros(len(byteBuffer[byteBufferLength-startIdx[0]:]),dtype = 'uint8')
                byteBufferLength = byteBufferLength - startIdx[0]
                
            # Check that there have no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0
                
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2**8, 2**16, 2**24]
            
            # Read the total packet length
            totalPacketLen = np.matmul(byteBuffer[12:12+4],word)
            
            # Check that all the packet has been read
            if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
                magicOK = 1
    
    if magicOK:
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2 ** 8, 2 ** 16, 2 ** 24]

            # Initialize the pointer index
            idX = 0

            # Read the header
            magicNumber = byteBuffer[idX:idX + 8]
            idX += 8
            version = format(np.matmul(byteBuffer[idX:idX + 4], word), 'x')
            idX += 4
            totalPacketLen = np.matmul(byteBuffer[idX:idX + 4], word)
            idX += 4
            platform = format(np.matmul(byteBuffer[idX:idX + 4], word), 'x')
            idX += 4
            frameNumber = np.matmul(byteBuffer[idX:idX + 4], word)
            idX += 4
            timeCpuCycles = np.matmul(byteBuffer[idX:idX + 4], word)
            idX += 4
            numDetectedObj = np.matmul(byteBuffer[idX:idX + 4], word)
            idX += 4
            numTLVs = np.matmul(byteBuffer[idX:idX + 4], word)
            idX += 4
            subFrameNumber = np.matmul(byteBuffer[idX:idX + 4], word)
            idX += 4
            print(subFrameNumber)

            # Read the TLV messages
            for tlvIdx in range(numTLVs):

                # word array to convert 4 bytes to a 32 bit number
                word = [1, 2 ** 8, 2 ** 16, 2 ** 24]

                # Check the header of the TLV message
                try:
                    tlv_type = np.matmul(byteBuffer[idX:idX + 4], word)
                    idX += 4
                    tlv_length = np.matmul(byteBuffer[idX:idX + 4], word)
                    idX += 4
                except:
                    pass

                # Read the data depending on the TLV message
                if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:

                    # word array to convert 4 bytes to a 16 bit number
                    word = [1, 2 ** 8]
                    tlv_numObj = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2
                    tlv_xyzQFormat = 2 ** np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2

                    # Initialize the arrays
                    rangeIdx = np.zeros(tlv_numObj, dtype='int16')
                    dopplerIdx = np.zeros(tlv_numObj, dtype='int16')
                    peakVal = np.zeros(tlv_numObj, dtype='int16')
                    x = np.zeros(tlv_numObj, dtype='int16')
                    y = np.zeros(tlv_numObj, dtype='int16')
                    z = np.zeros(tlv_numObj, dtype='int16')

                    for objectNum in range(tlv_numObj):
                        # Read the data for each object
                        rangeIdx[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                        idX += 2
                        dopplerIdx[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                        idX += 2
                        peakVal[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                        idX += 2
                        x[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                        idX += 2
                        y[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                        idX += 2
                        z[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                        idX += 2

                        print(idX)

                    # Make the necessary corrections and calculate the rest of the data
                    rangeVal = rangeIdx * configParameters["rangeIdxToMeters"]
                    dopplerIdx[dopplerIdx > (configParameters["numDopplerBins"] / 2 - 1)] = dopplerIdx[dopplerIdx > (
                            configParameters["numDopplerBins"] / 2 - 1)] - 65535
                    dopplerVal = dopplerIdx * configParameters["dopplerResolutionMps"]
                    x = x / tlv_xyzQFormat
                    y = y / tlv_xyzQFormat
                    z = z / tlv_xyzQFormat

                    # Store the data in the detObj dictionary
                    detObj = {"numObj": tlv_numObj, "rangeIdx": rangeIdx, "range": rangeVal, "dopplerIdx": dopplerIdx, \
                              "doppler": dopplerVal, "peakVal": peakVal, "x": x, "y": y, "z": z}
                    # print(detObj)
            # Remove already processed data
            try:
                if idX > 0 and byteBufferLength > idX:
                    shiftSize = totalPacketLen

                    byteBuffer[:byteBufferLength - shiftSize] = byteBuffer[shiftSize:byteBufferLength]
                    byteBuffer[byteBufferLength - shiftSize:] = np.zeros(len(byteBuffer[byteBufferLength - shiftSize:]),
                                                                         dtype='uint8')
                    byteBufferLength = byteBufferLength - shiftSize

                    # Check that there are no errors with the buffer length
                    if byteBufferLength < 0:
                        byteBufferLength = 0
            except:
                pass




        # Read the TLV messages
        # for tlvIdx in range(numTLVs):
            
        #     # word array to convert 4 bytes to a 32 bit number
        #     word = [1, 2**8, 2**16, 2**24]

        #     # Check the header of the TLV message
        #     tlv_type = np.matmul(byteBuffer[idX:idX+4],word)
        #     idX += 4
        #     tlv_length = np.matmul(byteBuffer[idX:idX+4],word)
        #     idX += 4

        #     # Read the data depending on the TLV message
        #     if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:

        #         # Initialize the arrays
        #         x = np.zeros(numDetectedObj,dtype=np.float32)
        #         y = np.zeros(numDetectedObj,dtype=np.float32)
        #         z = np.zeros(numDetectedObj,dtype=np.float32)
        #         velocity = np.zeros(numDetectedObj,dtype=np.float32)
                
        #         for objectNum in range(numDetectedObj):
                    
        #             # Read the data for each object
        #             x[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
        #             idX += 4
        #             y[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
        #             idX += 4
        #             z[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
        #             idX += 4
        #             velocity[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
        #             idX += 4
                
        #         # Store the data in the detObj dictionary
        #         detObj = {"numObj": numDetectedObj, "x": x, "y": y, "z": z, "velocity":velocity}
        #         dataOK = 1
                
 
        # # Remove already processed data
        # if idX > 0 and byteBufferLength>idX:
        #     shiftSize = totalPacketLen
            
                
        #     byteBuffer[:byteBufferLength - shiftSize] = byteBuffer[shiftSize:byteBufferLength]
        #     byteBuffer[byteBufferLength - shiftSize:] = np.zeros(len(byteBuffer[byteBufferLength - shiftSize:]),dtype = 'uint8')
        #     byteBufferLength = byteBufferLength - shiftSize
            
        #     # Check that there are no errors with the buffer length
        #     if byteBufferLength < 0:
        #         byteBufferLength = 0    

        # if if_button_is_pushed == 1:
        #     time.sleep(0.02)
        #     slope = 1
        #     try: 
        #         counter = 0 
        #         next_frame = 0 
        #         for i in range(len(detObj['x'])): 
        #             print(i)     
        #     except Exception:
        #         traceback.print_exc()

    return dataOK, frameNumber, detObj

# ------------------------------------------------------------------

# Funtion to update the data and display in the plot
def update():
     
    dataOk = 0
    global detObj
    x = []
    y = []
      
    # Read and parse the received data
    dataOk, frameNumber, detObj = readAndParseData18xx(Dataport, configParameters)
    
    if dataOk and len(detObj["x"])>0:
        #print(detObj)
        x = -detObj["x"]
        y = detObj["y"]
        
        s.setData(x,y)
        QtGui.QApplication.processEvents()
    
    return dataOk


# -------------------------    MAIN   -----------------------------------------  

# Configurate the serial port
CLIport, Dataport = serialConfig(configFileName)

# Get the configuration parameters from the configuration file
configParameters = parseConfigFile(configFileName)

# START QtAPPfor the plot
app = QtGui.QApplication([])

# Set the plot 
pg.setConfigOption('background','w')
win = pg.GraphicsLayoutWidget(title="2D scatter plot")
p = win.addPlot()
p.setXRange(-0.5,0.5)
p.setYRange(0,1.5)
p.setLabel('left',text = 'Y position (m)')
p.setLabel('bottom', text= 'X position (m)')
s = p.plot([],[],pen=None,symbol='o')
win.show()
   
# Main loop 
detObj = {}  
frameData = {}    
currentIndex = 0


while True:
    # k = readkey()

    try:
        # et = input("")
        # et = "testing"
        # print(f"You entered a command:{et} -> s: save, p: preview")
        # Update the data and check if the data is okay
        dataOk = update()
        
        if dataOk:
            # Store the current frame into frameData
            frameData[currentIndex] = detObj
            currentIndex += 1
            print(frameData[0])
        
        time.sleep(0.05) # Sampling frequency of 30 Hz
        
    # Stop the program and close everything if Ctrl + c is pressed
    # except KeyboardInterrupt:
    except Exception:
        CLIport.write(('sensorStop\n').encode())
        CLIport.close()
        Dataport.close()
        win.close()
        break
        
    





