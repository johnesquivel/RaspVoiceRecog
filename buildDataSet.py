__author__ = 'johne'


from serial import Serial
from struct import pack, unpack
from scipy.fftpack import fft
import sys
import os
import shutil
import array as ar
import numpy as np
import wave


def normalize(inData):
    snd_data = np.array(inData, 'float')
    # Remove the mean from the data
    snd_data = snd_data - snd_data.mean()
    # Scale to max amplitude
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = ar.array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r


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


def sectionWav(signal, qrt):
   segSig = np.zeros([4, qrt])
   segSig[0,:] = signal[0:qrt]
   segSig[1,:] = signal[qrt:qrt*2]
   segSig[2,:] = signal[qrt*2:qrt*3]
   segSig[3,:] = signal[qrt*3:qrt*4]
   return segSig


# Divide the audio wave into 4 sections,
# FFT each section, then
# Concatenate the 1st half of each fft into one fftArray.
def fftMyWav(din, n):
    fftArray = np.zeros(n/2) # Ending array is 1/2 size of input wave
    segSig = sectionWav(din, n/4) # Split into 4 sections

    for i in range(4):
        yf = np.abs(fft(segSig[i,:])) # FFT each section
        fftArray[i*(n/8) : (i+1)*(n/8)] = yf[0:n/8] # Concate upper halves together
    return fftArray


def saveAsTxt(dataFFT, prefix, workingDir, i):
   # Write the fft data to file
   fileName = workingDir + '/' + prefix + '/' + prefix + '_' + str(i) + '.txt'
   f = open(fileName, 'w')
   for j in range(len(dataFFT)):
      f.write(str(int(dataFFT[j])) + '\n')
   f.close()


def saveAsWav(data, prefix, workingDir, i):
    # Save each sample as a .wav file for review
    ## NEED to use OS.path.join
    path = workingDir + '/' + prefix + '/' + prefix + '_' + str(i) + '.wav'
    data = pack('<' + ('h'*len(data)), *data)
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(6804)
    wf.writeframes(data)
    wf.close()


def askForPnN():
    """
    Asks how many samples to take and the name of
    the directory to place the results in.
    :int, string : numOfSamples, prefix
    """
    print "\n\n"
    try:
        nSamples = int(raw_input('How many samples do you want to take:'))
    except ValueError:
        print "Not a number"
        sys.exit(0)

    # Ask what prefix to use for the data files
    print '\n'
    prefix = raw_input('What prefix should I use for the files:')
    return (nSamples, prefix)


def createResultsDir(prefix, workingDir):
    # Create the dir to store the results
    directory = workingDir + "/" + prefix
     # Clear the data directory if it exists, then create it anew
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)


def buildDataSet(mySerialPort, numOfPoints, workingDir):
    # Ask user for # of samples and prefix of dir
    (numOfSamples, prefix) = askForPnN()
    # Create the dir to store the results
    createResultsDir(prefix, workingDir)

    # Now create nSample files with the results
    for i in range(0, numOfSamples, 1):
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
        saveAsWav(dataNorm, prefix, workingDir, i)
        dataFFT = fftMyWav(dataNorm, numOfPoints)
        saveAsTxt(dataFFT, prefix, workingDir, i)

        print "\nGot it. " + str(numOfSamples - i - 1) + " samples left to go."
    return numOfSamples

if __name__ == '__main__':
    # buildDataSet.py executed as a script
    buildDataSet("portName", 1, "myDir")
