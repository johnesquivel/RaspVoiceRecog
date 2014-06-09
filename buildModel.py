__author__ = 'johne'

import numpy as np
import sys, wave, struct
from sklearn.metrics             import precision_score, recall_score, confusion_matrix
from pybrain.datasets            import ClassificationDataSet
from pybrain.utilities           import percentError
from pybrain.tools.shortcuts     import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.structure.modules   import SoftmaxLayer
from time import time
import datetime

if sys.platform == 'darwin':
    # On Mac
    from pybrain.tools.xml.networkwriter import NetworkWriter
else:
    # On Raspberry Pi
    from pybrain.tools.customxml.networkwriter import NetworkWriter

# Open a wave file and return the data
def openWave(filePath):
   waveFile = wave.open(filePath, 'r')
   length = waveFile.getnframes()
   waveData = waveFile.readframes(length)
   waveFile.close()
   data = struct.unpack('<' + ('h' * length), waveData)
   return data



def createRGBdataSet(inputSet, numOfSamples, numOfPoints):
    alldata = ClassificationDataSet(numOfPoints, 1, nb_classes=3)
    # Iter through all 3 groups and add the samples with appropriate class label
    for i in range(0, 3*numOfSamples):
        input = inputSet[i]
        if (i < numOfSamples):
            alldata.addSample(input, [0])
        elif (i >= numOfSamples and i < numOfSamples*2):
            alldata.addSample(input, [1])
        else:
            alldata.addSample(input, [2])
    return alldata


# Split the dataset into 75% training and 25% test data.
def splitData(alldata):
    tstdata, trndata = alldata.splitWithProportion( 0.25 )
    trndata._convertToOneOfMany()
    tstdata._convertToOneOfMany()
    return trndata, tstdata


# Print out the precision, recall and the confusion matrix for alldata
def checkNeuralNet(trainer, alldata, numOfSamples):
    # Predicted and actual values for measuring performance
    y_pred = trainer.testOnClassData(alldata)
    y_true = [0]*numOfSamples + [1]*numOfSamples + [2]*numOfSamples
    # Performance metrics
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    # Print the metrics
    print("\nThe precision = %1.3f" % precision)
    print("The recall = %1.3f" % recall)
    print("\nThe confusion matrix is as shown below:")
    print(confusion_matrix(y_true, y_pred))


def trainNetwork(inData, numOfSamples, numOfPoints, epochs):
    # Build the dataset
    alldata = createRGBdataSet(inData, numOfSamples, numOfPoints)
    # Split into test and training data
    trndata, tstdata = splitData(alldata)

    # Report  stats
    print "Number of training patterns: ", len(trndata)
    print "Input and output dimensions: ", trndata.indim, trndata.outdim
    print "First sample (input, target, class):"
    print trndata['input'][0], trndata['target'][0], trndata['class'][0]

    # Build and train the network
    fnn = buildNetwork( trndata.indim, 256, trndata.outdim, outclass=SoftmaxLayer )
    trainer = BackpropTrainer( fnn, dataset=trndata, momentum=0.001, verbose=True, weightdecay=0.001)
    #trainer.trainEpochs( epochs )
    trainer.trainUntilConvergence(maxEpochs=epochs)

    # Report results
    trnresult = percentError( trainer.testOnClassData(), trndata['class'] )
    tstresult = percentError( trainer.testOnClassData( dataset=tstdata ), tstdata['class'] )
    print "epoch: %4d" % trainer.totalepochs, \
      "  train error: %5.2f%%" % trnresult, \
      "  test error: %5.2f%%" % tstresult

    # Report results of final network
    checkNeuralNet(trainer, alldata, numOfSamples)
    return fnn


def readRGBData(workingDir, numOfSamples, numOfPoints):
    listOfDirs = ["red", "green", "blue"]
    # Dataset to return
    samples = 3 * numOfSamples
    fftData = np.zeros([samples, numOfPoints])

    # Iterate though color directories
    row = 0
    for color in listOfDirs:
        for i in range(0, numOfSamples):
            fileName = workingDir + '/' + color + '/' + color + '_' + str(i) + '.txt'
            f = open(fileName, 'r')
            for col in range(0, numOfPoints):
                try:
                    fftPoint = f.readline(10)
                    fftData[row, col] = fftPoint
                except ValueError:
                    print "ValueError: Line " + str(col) + ", read " + fftPoint
                    sys.exit(0)

            f.close()
            row += 1
    return fftData


def printRGBData(fftData, numOfSamples, numOfPoints, workingDir):
    f = open(workingDir + '/classFile.csv', 'w')
    # Print feature labels
    for j in range(0, numOfPoints):
        f.write('B' + str(j) + ',')
    f.write("Class\n")

    # Print the data
    for row in range(0, 3*numOfSamples):
        for col in range(0, numOfPoints):
            f.write( '%5d, ' % fftData[row, col] )
        if (row < numOfSamples):
            f.write('Red\n')
        elif (row >= numOfSamples and row < 2*numOfSamples):
            f.write('Green\n')
        else:
            f.write('Blue\n')
    f.close()


def hms_to_seconds(t):
    h, m, s = [int(i) for i in t.split(':')]
    return 3600*h + 60*m + s

# Build the classification model.
# numOfPoints is the number of data points in each file
def buildModel(numOfPoints, workingDir):
    # Ask what action they want to do
    print "\nAlright, lets build the model.\n"
    try:
        numOfSamples = int(raw_input("How many samples per class: "))
    except ValueError:
        print "Not a number"
        sys.exit(0)

    try:
        epochs = int(raw_input("Max training iterations: "))
    except ValueError:
        print "Not a number"
        sys.exit(0)

    fftData = readRGBData(workingDir, numOfSamples, numOfPoints/2)  # Read sample data
    printRGBData(fftData, numOfSamples, numOfPoints/2, workingDir)     # Export data for external testing is desired
    # Train the backprop network and time how long it takes
    t0 = time()
    fnn = trainNetwork(fftData, numOfSamples, numOfPoints/2, epochs)
    t1 = time()
    print 'It took %s to build the NN' % str(datetime.timedelta(seconds=(t1-t0)))
    # Save backprop net using NetworkWriter
    NetworkWriter.writeToFile(fnn, workingDir + '/fnn.xml')


if __name__ == '__main__':
   # Execute buildModel as a script
    buildModel(1, '/')


