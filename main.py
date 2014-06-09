__author__ = 'johne'

import buildDataSet
import buildModel
import useModel
import sys



if __name__ == '__main__':

    ########## Settings that user needs to change ###########
    # Number of points to sample
    numOfPoints = 2048;
    # Serial port though which you communicate with Arduino
    #mySerialPort = '/dev/ttyUSB0';
    mySerialPort = '/dev/tty.usbserial-AD01THOK'
    workingDir = '/Users/johne/data'
    #########################################################


    # MAIN PROGRAM

    while True:
        # Ask what action they want to do
        print "\n\nWhat activity do you wish to do?"
        print "0. Exit the program"
        print "1. Record samples for a dataset"
        print "2. Build a back-propagation model"
        print "3. Use current prediction model"
        try:
            actionNum = int(raw_input("\nEnter your selection: "))
        except ValueError:
            print "Not a number"
            sys.exit(0)

        if (actionNum==0):
            sys.exit(0)
        if (actionNum==1):
            buildDataSet.buildDataSet(mySerialPort, numOfPoints, workingDir)
        elif (actionNum==2):
            buildModel.buildModel(numOfPoints, workingDir)
        elif (actionNum==3):
            useModel.monitorAudio(mySerialPort, numOfPoints, workingDir)


