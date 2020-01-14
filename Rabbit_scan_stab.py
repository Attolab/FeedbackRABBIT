# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 14:26:17 2019

@author: mluttmann
"""

"""

"""


import time


import os

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.uic import loadUiType




# TODO :
# 1) the scanning loop does NOT stop when quitting the application !!!!!
# 2) add a moveAbolute signal to the ScanningLoop to send the smarAct to the start position ???

"""
class handling the scan operations
"""
class ScanningStabLoop(QtCore.QObject):
    scanStabFinished = QtCore.pyqtSignal()
    requestSSMotion = QtCore.pyqtSignal(int)  #signal request stabilized scan step
    requestStopSSMotion = QtCore.pyqtSignal()
    changeTimeSignal = QtCore.pyqtSignal()  #new remaining time required
    requestScopeMemoryClear = QtCore.pyqtSignal()
    setScopeMode = QtCore.pyqtSignal(int)
    requestEmitDataReconnection = QtCore.pyqtSignal()
    def __init__(self, middle, step, nbrOfPoints, direction, folder, Tab3, step_duration):
        super(ScanningStabLoop, self).__init__()
        
        self.tab3 = Tab3
        self.nbrOfPoints = nbrOfPoints
        self.stepDuration = step_duration   #in nbr of acquisitions
        self.step = int(step)
        
        self.totalDuration = self.nbrOfPoints*self.stepDuration
        
        if direction == "Backward":
            self.step = -self.step
        
        self.start = middle - (self.step*self.nbrOfPoints)/2
        self.stabPos = self.start  #position where to stabilize the interferometer
        self.folder = folder
        self.data = []
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()

        # start the scanning loop
        self.SSrun = True
        
        self.nextStepAllowed = False
        
        self.scanStabTime = 0  #in number of steps
        
        self.acqScanTime = 0  #in number of acquisitions

    def Run(self):
        # move to the intial position and wait until initial position is reached
        '''
        print("begin Scan Stab Run")
        self.mutex.lock()
        print("after mutex lock")
        self.requestSSMotion.emit(self.stabPos)
        print("after request motion")
        self.smarActStopCondition.wait(self.mutex)
        print("after smaractstopcondition wait")
        self.mutex.unlock()
        print("after unlock mutex")
        '''
        for ii in range(self.nbrOfPoints):
#            # clear scope memory
#            print('clear memory')
#            self.requestScopeMemoryClear.emit()
            if not self.SSrun:
                print("BREAK SS LOOP")
                break            
            # freeze this loop while the stage is not at destination :
            print('')
            
            #self.mutex.lock()
            print("begin scan stab step")
            
            
            
            self.requestSSMotion.emit(self.stabPos)

            ################ wait during step duration ##################
            #self.thread().msleep(self.stepDuration*1000)  #in milliseconds
            while not self.nextStepAllowed:
                print("waiting for next step allowance")
                self.thread().msleep(100)
                if not self.SSrun:
                    break
            #python internal clock
            #self.requestStopSSMotion.emit()
            self.nextStepAllowed = False
            
            #self.smarActStopCondition.wait(self.mutex)
            print("after .wait in scan stab")
            #self.mutex.unlock()
            
            self.stabPos = self.tab3.stageWidget.PositionNmLCD.value() + self.step
            
            
            self.changeTimeSignal.emit()
            
            # allow data emition fro mthe scopeWidget
            #self.requestEmitDataReconnection.emit()
            # trigger scope
            #self.setScopeMode.emit(0)
            '''
            # read scope
            print('Waiting')
            while self.data == []:
                self.thread().msleep(500)
            
            self.requestScopeMemoryClear.emit()
            '''
            
            '''
            #write data to file
            index = str(ii)
            index = (4-len(index)) * "0" + index
            fileName = "ScanFile" + index + ".txt"

            pathFile = os.path.join(self.folder, fileName)
            file = open(pathFile,"w")
            for ii in range(len(self.data[0])):
                file.write('%f\t%f\n' % (self.data[0][ii], self.data[1][ii]))
            file.close()
            self.StoreData([])
            '''
            self.scanStabTime += self.stepDuration
            
        self.scanStabFinished.emit()
        
        

        
    '''
    def StoreData(self, data):
        self.data = data
        if data != []:
            # stop the scope while the main loop write the data in a file
            self.setScopeMode.emit(3)
        '''
        
    def Stop(self):
        self.SSrun = False
            


"""
Scan Stab Widget class
"""
qtCreatorFile = "ScanStabPyQt5UI.ui"
Ui_StopScanStabWidget, QtBaseClass = loadUiType(qtCreatorFile)
class ScanStabWidget(QtWidgets.QFrame, Ui_StopScanStabWidget):
    def __init__(self, Tab3, mode):
        QtWidgets.QFrame.__init__(self, parent=None)
        self.setupUi(self)
        
        self.tab3 = Tab3
        self.stepDurationSpinBox.setValue(10)  #by default 10 s steps
        
        self.centralPosSpinBox.setValue(1000)
        self.stepSizeSpinBox.setValue(20)
        self.nbrPointsSpinBox.setValue(20)
        
        
        self.mode = mode
        
        self.startScanPushButton.clicked.connect(self.StartStopScanStab)
        
        
        ############### need activate deactivate SS #############
        
        self.scanGroupBox.setEnabled(True)
        self.startScanPushButton.setEnabled(True)
        
    def CheckDataFolderExistance(self):
        folderName = self.dataFolderEdit.text()
        if not os.path.exists(folderName):
            reply = QtWidgets.QMessageBox.question(self, "Message",
                                                   "The specified data folder does NOT exist. Do you want to create it?", QtWidgets.QMessageBox.Yes | 
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                os.makedirs(folderName)
            else:
                return "Cancel stabilized scan"
        return "Proceed"


    def StartStopScanStab(self, scanOn):
        
        if scanOn:
            self.CheckDataFolderExistance()
            # block interaction with the controls
            self.startScanPushButton.setText("Stop Stabilized Scan")
            self.scanGroupBox.setEnabled(False)
            #self.scopeWidget.setEnabled(False)
            #self.stageWidget.setEnabled(False)
            # Reinitialize the matshow display
            #self.TwoDPlotDraw([[0,0],[0,0]])
            # stop the scope trigger and clear the scope memory
            #self.scopeWidget.triggerModeComboBox.setCurrentIndex(3)
            #self.scopeWidget.ClearSweeps()
            # create a scanning loop
            
            t0 = time.perf_counter()    #time given by the processor internal clock
            
            # middle, step, nbrOfPoints, direction, folder, Tab3, step_duration
            self.scanningStabLoop  = ScanningStabLoop(self.centralPosSpinBox.value(),
                                             self.stepSizeSpinBox.value(),
                                             self.nbrPointsSpinBox.value(),
                                             self.mvtTypeComboBox.currentText(),
                                             self.dataFolderEdit.text(),
                                             self.tab3,
                                             self.stepDurationSpinBox.value())
            # create and start the scanning thread
            
            
            self.timeLCD.display(self.scanningStabLoop.totalDuration)
            self.scanningStabThread = QtCore.QThread()
            self.scanningStabLoop.moveToThread(self.scanningStabThread)
            self.ConnectScanStabSignals()
            print("thread start")
            self.scanningStabThread.start()

        else:
            reply = QtWidgets.QMessageBox.question(self, 'Message', "Do you want to stop the stabilized scan?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.scanningStabLoop.Stop()
                #self.EndOfStabScan()

        
    def stabilize_at(self, position):
        
        
        self.tab3.locking_position_display.setText(str(position))
        self.tab3.shapedErrorPlotDraw()
        self.tab3.tMax = self.scanningStabLoop.stepDuration
        
        if self.mode == "test scan stab":        
            self.tab3.testStabScanBtnClicked.emit(True)
            self.tab3.launch_feedback_test_btn.setChecked(True)
            print("after checked button true")
        if self.mode == "scan stab":
            self.tab3.stabScanBtnClicked.emit(True)
            self.tab3.launch_feedback_btn.setChecked(True)
            print("after checked button true")           
            

    def stopStabilize(self):
        self.tab3.launch_feedback_test_btn.setChecked(False)
        #self.tab3.checkFeedback()
        self.tab3.feedback_time = 0
        #time.sleep(1.)
        #self.scanningStabLoop.stabPos += self.scanningStabLoop.step


    def allowNextStep(self):
        self.scanningStabLoop.nextStepAllowed = True
        print("NEXT STAB SCAN STEP ALLOWED")


    def changeTimeDisplay(self):
        
        t = self.timeLCD.value()
        new_t = t - self.scanningStabLoop.stepDuration
        self.timeLCD.display(new_t)


    def changeProgressBar(self, time):
                self.scanningStabLoop.acqScanTime += 1
                self.CurrentStepProgressBar.setValue((time/self.scanningStabLoop.stepDuration)*100)
                self.ScanProgressBar.setValue((self.scanningStabLoop.acqScanTime/self.scanningStabLoop.totalDuration)*100)
                
    def EndOfStabScan(self):
        scanStabStatus = self.DisconnectScanStabSignals()
        if scanStabStatus != "Cancel stabilized scan":
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.startScanPushButton.blockSignals(True)
            self.startScanPushButton.setChecked(False)
            self.startScanPushButton.blockSignals(False)
            self.startScanPushButton.setText("Start Stabilized Scan")
            self.tab3.launch_feedback_test_btn.setChecked(False)
            
            self.scanningStabThread.exit()
            
            print("exit scanningStabThread")
            # wait for the thread exit before going on :
            while self.scanningStabThread.isRunning():
                print("wait for SS thread to end")
                self.thread().msleep(100)
        #reenable the user inteface
   

        self.scanGroupBox.setEnabled(True)

    def ConnectScanStabSignals(self):
        
        self.scanningStabLoop.requestSSMotion.connect(self.stabilize_at)
        
        self.scanningStabLoop.requestStopSSMotion.connect(self.stopStabilize)
        
        
        self.scanningStabLoop.changeTimeSignal.connect(self.changeTimeDisplay)
        self.tab3.stepPercentSignal.connect(self.changeProgressBar)
        #self.stageWidget.smarActReader.motionEnded.connect(self.scanningLoop.smarActStopCondition.wakeAll)
        # Allow the scanningLoop to set the scope trigger mode
        
        #self.scanningLoop.setScopeMode.connect(self.scopeWidget.triggerModeComboBox.setCurrentIndex)
        
        # Allow the scanningLoop to clear the scope memory after motion :
        #self.scanningLoop.requestScopeMemoryClear.connect(self.scopeWidget.ClearSweeps)
        # connect the scanning loop Run function to the scanning thread start
        
        self.scanningStabThread.started.connect(self.scanningStabLoop.Run)
        # connect the scanningLoop 
        #self.scanningStabLoop.requestEmitDataReconnection.connect(self.ConnectDisplay)
        # ... and wait for the end of the scan :
        self.scanningStabLoop.scanStabFinished.connect(self.EndOfStabScan)
        
        
        self.tab3.stepOfStabScanFinished.connect(self.allowNextStep)



    '''
    def ConnectDisplay(self):
        print('a')
        self.scopeWidget.emitData.connect(self.ForwardData)
        print('b')
        
        '''
        
        
    
    def DisconnectScanStabSignals(self):
        self.scanningStabLoop.requestSSMotion.disconnect()
        self.scanningStabLoop.requestStopSSMotion.disconnect()
        #self.stageWidget.smarActReader.motionEnded.disconnect()
        #self.scanningLoop.requestScopeMemoryClear.disconnect()
        self.scanningStabThread.started.disconnect()
        self.scanningStabLoop.scanStabFinished.disconnect()
        #self.ConnectDisplay()
