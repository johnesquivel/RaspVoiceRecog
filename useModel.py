__author__ = 'johne'

import sys
from serial import Serial
from buildDataSet import normalize
from buildDataSet import fftMyWav
import array as ar
from struct import pack, unpack
from time import sleep


if sys.platform == 'darwin':
    # On Mac
    from pybrain.tools.xml.networkreader import NetworkReader
else:
    # On Raspberry Pi
    from pybrain.tools.customxml.networkreader import NetworkReader
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # Setup GPIOs as outputs
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.OUT)
    GPIO.setup(25, GPIO.OUT)


# Function to read the serial port
def readPacket(port):
    # Create packet to hold all 8 int values
    packet = ar.array('i',range(4))
    # Start reading indefinitely
    while True:
        # Keeping reading till we find the 'H' char
        ch = port.read()
        if ch == 'H':
            # Once 'H' is found then read 8 bytes
            for i in range(0, 4):
                x = port.read()
                #x1 = port.read()
                if (len(x) > 0):
                    packet[i] = unpack('>h', b'\x00' + x)[0]
                else:
                    packet[i] = 0
            return packet


# Function to retrieve data from serial port
def getSerialData(n, port):
    # Create allPackets as an int array to hold all results
    allPackets = ar.array('i',range(n))
    # Read 8 values at a time using readPacket
    for i in range(0, n, 4):
        allPackets[i:i+4] = readPacket(port)
    return allPackets


def listenToSerial(mySerialPort, numOfPoints):
    # Listen to the serial port for data
    print "\nSpeak into the mic now\n"

    # Open the serial port
    port = Serial(mySerialPort, 230400, timeout=2.0)
    port.close()
    port.open()

    # Read results from serial line
    rawData = getSerialData(numOfPoints, port)

    # Close the serial port
    port.close()

    # Normalize the data and convert to FFT
    dataNorm = normalize(rawData)
    dataFFT = fftMyWav(dataNorm, numOfPoints)
    return dataFFT


def setLED(result):
    # Determine which value the net picked
    groups = ['Red', 'Green', 'Blue']
    groupID = max(xrange(len(result)), key=result.__getitem__)
    groupName = groups[groupID]

    if sys.platform == 'darwin':   # Determine os
        # Mac section
        print "\nResults matrix:"
        print result
        print "\n Detected = " + groupName,
        print " with %2.1f%% likelyhood" % (result[groupID]*100.0)
    else:
        # Raspberry Pi section
        # Print to scree the predicted result
        print "\n Detected = " + groupName,
        print " with %2.1f%% likelyhood" % (result[groupID]*100.0)
        if (groupID == 0):
            pinNum = 24
        elif (groupID == 1):
            pinNum = 23
        elif (groupID == 2):
            pinNum = 25
        GPIO.output(pinNum, True)
        sleep(2.0)
        GPIO.output(pinNum, False)


def monitorAudio(mySerialPort, numOfPoints, workingDir):
    # Load the neural network model
    net = NetworkReader.readFrom(workingDir + '/fnn.xml')
    while True:
        # Record audio sample
        dataFFT = listenToSerial(mySerialPort, numOfPoints)
        # Process new sample thru NN
        result = net.activate(dataFFT)
        # Present prediction result
        setLED(result)


if __name__ == '__main__':
    # Call useModel as a script
    monitorAudio('portName', 'dir', 1)
