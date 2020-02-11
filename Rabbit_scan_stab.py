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

import datetime

class ScanningStabLoop(QtCore.QObject):
    scanStabFinished = QtCore.pyqtSignal()
    requestSSMotion = QtCore.pyqtSignal(int)  #signal request stabilized scan step
    #requestStopSSMotion = QtCore.pyqtSignal()
    launchFeedbackSignal = QtCore.pyqtSignal(int)
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
        
        self.start = int(middle - (self.step*self.nbrOfPoints)/2)
        self.stabPos = self.start  #position where to stabilize the interferometer
        self.folder = folder
        self.data = []
        
        
        
        self.mutex = QtCore.QMutex()
        self.feedbackStepWait = QtCore.QWaitCondition()

        # start the scanning loop
        self.SSrun = True
        
        self.nextStepAllowed = True
        
        self.scanStabTime = 0  #in number of steps
        
        self.acqScanTime = 0  #in number of acquisitions
        

        
        
        
        
        
    def Run(self):
        
        self.CheckFolders()

        self.launchFeedbackSignal.emit(self.stabPos)
        
        print("begin Scan Stab Run")
 
        self.thread().msleep(1000)
        feedbackTime = 0
        currentFolder = self.StabScanFolder+"/Step_"+str(self.stabScanStepNbr)        
        os.mkdir(currentFolder)  

        ################ creates a file with the parameters of the scan ###################
        
        self.writeParam()
        
        
        
        while feedbackTime < self.totalDuration:
            # clear scope memory
            #print('clear memory')
            #self.requestScopeMemoryClear.emit()
            if not self.SSrun:
                print("BREAK SS LOOP")
                break            
            # freeze this loop while the stage is not at destination :
            #print('')

            self.tab3.storedatafolder = currentFolder 
            
            self.mutex.lock()
   
       
      
            self.feedbackStepWait.wait(self.mutex)
     
            self.mutex.unlock()
            
            
            feedbackTime = self.tab3.feedback_time
            #print("lock position = ", self.stabPos)            


            ################ wait during step duration ##################
            #self.thread().msleep(self.stepDuration*1000)  #in milliseconds
            #self.mutex.lock
            
            
            #print("feedback time read in SS loop = ", feedbackTime)
            
            if (feedbackTime%self.stepDuration == 0) and (feedbackTime != 0):  #request step when the number of acq. per step is reached
                self.stabPos += self.step
                self.tab3.requestSSMotion.emit(self.stabPos)                
               
                #print("recquire new stab scan locking pos")

                
                self.stabScanStepNbr += 1
                currentFolder = self.StabScanFolder+"/Step_"+str(self.stabScanStepNbr)
                os.mkdir(currentFolder)


                self.thread().msleep(100)
            self.thread().msleep(100)                
            '''
            while not self.nextStepAllowed:
                print("waiting for next step allowance")
                self.thread().msleep(100)
                if not self.SSrun:
                    break
            '''

            self.scanStabTime += self.stepDuration
            self.changeTimeSignal.emit()
            # 21-01-2020
            #self.tab3.stepOfStabScanFinished.emit()
 
        self.tab3.stabScanNbr += 1           
        self.scanStabFinished.emit()
        print("end of the scan stab loop")

        

        
    '''
    def StoreData(self, data):
        self.data = data
        if data != []:
            # stop the scope while the main loop write the data in a file
            self.setScopeMode.emit(3)
        '''
        
    def Stop(self):
        self.SSrun = False
 

    def CheckFolders(self):
        self.StabScanFolder = self.folder+"/RAStaScan_"+str(self.tab3.stabScanNbr)
        
        self.stabScanStepNbr = 1
        
        if os.path.isdir(self.StabScanFolder):
            print("file already exists")
            self.StabScanFolder+="bis"
      
        
        os.mkdir(self.StabScanFolder)

    
    def writeParam(self):
        fileName = "RAStaScan_"+str(self.tab3.stabScanNbr)+"_param"+".txt"
    
        pathFile = os.path.join(self.StabScanFolder, fileName)
        file = open(pathFile,"w")
        
        file.write("Parameters of RASta scan "+str(self.tab3.stabScanNbr)+"\n")
        file.write("\n")
        file.write("Nbr of steps = "+str(self.nbrOfPoints)+"\n")
        file.write("Starting position (nm) = "+str(self.start)+"\n")               
        file.write("Step size (nm) = "+str(self.step)+"\n")                

        file.write("Initial Kp, Ki, Kd = "+str(self.tab3.Kp)+", "+str(self.tab3.Kd)+", "+str(self.tab3.Ki)+"\n")
        x = datetime.datetime.now()
        file.write("Date and time = "+str(x)+"\n") 
           
        file.write("\n SCOPE PARAMETERS \n") 
        file.write("Trigger mode = "+str(self.tab3.tab1.scopeWidget.reader.mode)+"\n")
        file.write("Nbr of segments = "+str(self.tab3.tab1.scopeWidget.reader.numSegments)+"\n")        
        #file.write("Nbr of points averaged = "+str()+"\n")
        file.write("Horizontal scale = "+str(self.tab3.tab1.scopeWidget.XScale)+"\n") 
        file.write("Vertical scale = "+str(self.tab3.tab1.scopeWidget.YScale)+"\n") 
        file.write("Horizontal offset = "+str(self.tab3.tab1.scopeWidget.XOffset)+"\n")
        file.write("Vertical offset = "+str(self.tab3.tab1.scopeWidget.YOffset)+"\n")  

        file.write("\n SMARACT PARAMETERS \n")
        #file.write("Controller ref. = "+str(self.tab3.tab1.stageWidget.chann)+"\n")
        file.write("Stage speed (nm/s). = "+str(self.tab3.tab1.stageWidget.SpeedSpinBox.value())+"\n")
         
        file.close()



           


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
        self.stepDurationSpinBox.setValue(10)  #by default 10 acq. steps
        
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
        
        self.tab3.stabScanNbr = self.ScanNbrSpinBox.value()  
        
        
        
        if scanOn:
            self.CheckDataFolderExistance()
            # block interaction with the controls
            self.startScanPushButton.setText("Stop Stabilized Scan")
            self.scanGroupBox.setEnabled(False)
 
            
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

    def launchFeedback(self, position):
        self.tab3.locking_position_display.setText(str(position))   
        self.tab3.shapedErrorPlotDraw()
        self.tab3.tMax = 100000
         
        if self.mode == "test scan stab":        
            self.tab3.testStabScanBtnClicked.emit(True)
            self.tab3.launch_feedback_test_btn.setChecked(True)
            print("after launch btn checked")
        if self.mode == "scan stab":
            self.tab3.stabScanBtnClicked.emit(True)
            self.tab3.launch_feedback_btn.setChecked(True)
            print("after checked button true")   
                 
    '''     
    def changeLockPos(self, position):
        self.tab3.locking_position_display.setText(str(position))         
    '''
    ''' 
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
            '''

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
        new_t = t - 1
        self.timeLCD.display(new_t)


    def changeProgressBar(self, time):
                time2 = time%(self.scanningStabLoop.stepDuration)
                self.scanningStabLoop.acqScanTime += 1
                self.CurrentStepProgressBar.setValue((time2/self.scanningStabLoop.stepDuration)*100)
                self.ScanProgressBar.setValue((self.scanningStabLoop.acqScanTime/self.scanningStabLoop.totalDuration)*100)
                
    def EndOfStabScan(self):
        scanStabStatus = self.DisconnectScanStabSignals()
        if scanStabStatus != "Cancel stabilized scan":
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.startScanPushButton.blockSignals(True)
            self.startScanPushButton.setChecked(False)
            self.startScanPushButton.blockSignals(False)
            
            #### correct ending of the feedbackloop
            
            if self.mode == "test scan stab":
                self.tab3.testStabScanBtnClicked.emit(False)
                self.startScanPushButton.setText("Start Stabilized Scan")
                self.tab3.launch_feedback_test_btn.setChecked(False)
                self.tab3.launch_feedback_test_btn.setText("LAUNCH RABBIT \n FEEDBACK TEST")
                
            if self.mode == "scan stab":   
                self.tab3.StabScanBtnClicked.emit(False)
                self.startScanPushButton.setText("Start Stabilized Scan")
                self.tab3.launch_feedback_btn.setChecked(False)
                self.tab3.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")                
                
            self.scanningStabThread.exit()
            
               
           
            
            print("exit scanningStabThread")
            # wait for the thread exit before going on :
            while self.scanningStabThread.isRunning():
                print("wait for SS thread to end")
                self.thread().msleep(100)
        #reenable the user inteface
   

        self.scanGroupBox.setEnabled(True)

    def ConnectScanStabSignals(self):
        
        #self.scanningStabLoop.requestSSMotion.connect(self.changeLockPos)
        
        #self.scanningStabLoop.requestStopSSMotion.connect(self.stopStabilize)
        
        self.scanningStabLoop.launchFeedbackSignal.connect(self.launchFeedback)
        
        self.scanningStabLoop.changeTimeSignal.connect(self.changeTimeDisplay)
        self.tab3.stepPercentSignal.connect(self.changeProgressBar)
        self.tab3.feedbackStepFinished.connect(self.scanningStabLoop.feedbackStepWait.wakeAll)
        
        self.scanningStabThread.started.connect(self.scanningStabLoop.Run)
        # connect the scanningLoop 
        #self.scanningStabLoop.requestEmitDataReconnection.connect(self.ConnectDisplay)
        # ... and wait for the end of the scan :
        self.scanningStabLoop.scanStabFinished.connect(self.EndOfStabScan)
        
        
        #self.tab3.feedbackStepFinished.connect(self.allowNextStep)



    '''
    def ConnectDisplay(self):
        print('a')
        self.scopeWidget.emitData.connect(self.ForwardData)
        print('b')
        
        '''
        
        
    
    def DisconnectScanStabSignals(self):
        #self.scanningStabLoop.requestSSMotion.disconnect()
        #self.scanningStabLoop.requestStopSSMotion.disconnect()
        #self.stageWidget.smarActReader.motionEnded.disconnect()
        #self.scanningLoop.requestScopeMemoryClear.disconnect()
        self.scanningStabLoop.launchFeedbackSignal.disconnect()
        self.scanningStabThread.started.disconnect()
        self.scanningStabLoop.scanStabFinished.disconnect()
        #self.ConnectDisplay()
