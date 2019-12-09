"""The program has to be runned here"""





import sys
import os



import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon


#homemade modules
import live_win 
import sidebands_win
import feedback_win
#import scanStab_win
from Rabbit_scan import ScanningLoop
from Feedback_loop import FeedbackLoop



class RABBIT_feedback(QtWidgets.QTabWidget):
    
    requestMotion = QtCore.pyqtSignal(int)    
    
    def __init__(self, parent = None):  
        """ 
        Main window. The main window is composed of three tabs: Live, Sideband and Feedback. 
        Those tabs are created via three classes containing attributes and methods. 
        For instance, the FeedbackTab class (imported from feedback_win.py) contains parameters used for the feedback only (PID parameters, locking positions, etc.).
        The RABBIT_feedbak class uses data and parameters from all three tabs, and updates them thanks to the RABBIT_feedback updating methods.
        """
        super(RABBIT_feedback, self).__init__(parent)
        
    
        self.tab1 = live_win.LiveTab()
        self.tab2 = sidebands_win.SidebandsTab()
        self.tab3 = feedback_win.FeedbackTab(self.tab1.scopeWidget, self.tab1.stageWidget, self.tab2)
        #self.tab4 = scanStab_win.scanStabTab(self.tab3)
        
        self.addTab(self.tab1,"Live")
        self.addTab(self.tab2, "Sidebands")
        self.addTab(self.tab3, "Feedback")
        #self.addTab(self.tab4, "Stab scan")
        
        self.setWindowTitle("RABBIT Active Stabilization")
        self.setWindowIcon(QIcon("icon_rasta.png") )
        
        self.setGeometry(100, 100, 1510, 1000)
        
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()
        
        self.canMove = False
        

        
        self.period = 1. #s, period of the feedback loop
        self.tStart = int(3/self.period)
        self.tab3.T = self.period #ins, period in the PID controller       
        
        
        
        self.tGlob = 0
        
        # prepare the transmission of the data to the graphs (will also be used by the scanning loop)
        self.ConnectDisplay()
        # activate/deactivate widgets controls in agreement with the current configuation :
        # 1) Alow scan control if both scope and stage are running :
        self.tab1.scopeWidget.scopeGroupBox.toggled.connect(self.ActivateDeactivateScan)
        self.tab1.stageWidget.ChannelComboBox.currentIndexChanged.connect(self.ActivateDeactivateScan)
        self.tab1.scopeWidget.scopeGroupBox.toggled.connect(self.ActivateDeactivateFeedback)
        self.tab1.stageWidget.ChannelComboBox.currentIndexChanged.connect(self.ActivateDeactivateFeedback)
        # 2) disable controls duing the scan : 
        self.tab1.scanWidget.startScanPushButton.clicked.connect(self.StartStopScan)
        self.tab3.launch_feedback_btn.clicked.connect(lambda x : self.StartStopFeedback(x, "Feedback"))
        self.tab3.launch_feedback_test_btn.clicked.connect(lambda x : self.StartStopFeedback(x, "Test Feedback"))        
        
        self.tab3.testStabScanBtnClicked.connect(lambda x : self.StartStopFeedback(x, "Test Feedback"))
        self.tab3.stabScanBtnClicked.connect(lambda x : self.StartStopFeedback(x, "Feedback"))
        
        self.show()
        
    #################################################################################################    
    ################################## RABBIT FEEDBACK FUNCTIONS ############################################
        
        
    def DisplayAndStabilize(self, data):  #updates the scope windows (scope 1, scope 2, time error plot and time delay position) and performs feedback
        scale_y=self.tab1.scopeWidget.YScale
        scale_x=self.tab1.scopeWidget.XScale
        y_offset = self.tab1.scopeWidget.YOffset
        x_offset = self.tab1.scopeWidget.XOffset
        

        ########### updates scope screen in tab 1 ################
        self.tab1.updateLiveScreen(data, scale_x, scale_y, x_offset, y_offset)
        
        ########### updates screens in tab 3 ################

        print("")
        print("DISPLAY")
        print("")
        #if self.tGlob%1 == 0: #☻doesnt update all the time during feedback
        self.tab3.updateFeedbackScreens(data, scale_x, scale_y, x_offset, y_offset)

        self.tGlob += 1

    
  
    ################################## RABBIT scan ############################################
        
    def ActivateDeactivateScan(self):
        # enable/diable the "start scan" button ont he scan widget depending on the other widgets states 
        scopeOn = self.tab1.scopeWidget.scopeGroupBox.isChecked()
        stageOn = self.tab1.stageWidget.ChannelComboBox.currentIndex()>0
        if scopeOn and stageOn:
            self.tab1.scanWidget.startScanPushButton.setEnabled(True)
            self.tab1.scanWidget.scanGroupBox.setEnabled(True)
        else:
            self.tab1.scanWidget.startScanPushButton.setEnabled(False)
            self.tab1.scanWidget.scanGroupBox.setEnabled(False)
    
    def CheckDataFolderExistance(self):
        folderName = self.tab1.scanWidget.dataFolderEdit.text()
        if not os.path.exists(folderName):
            reply = QtWidgets.QMessageBox.question(self, "Message",
                                                   "The specified data folder does NOT exist. Do you want to create it?", QtWidgets.QMessageBox.Yes | 
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                os.makedirs(folderName)
            else:
                return "Cancel scan"
        return "Proceed"
                
    def ForwardData(self, data):
        #print("forwarddata")
        if self.tab1.scanWidget.startScanPushButton.isChecked():
            # during a scan : transmit the data to the scanningLoop object and disable the conection to prevent multiple acquisition at a single delay
            self.tab1.scopeWidget.emitData.disconnect()
            self.scanningLoop.StoreData(data)
        
        if self.tab3.launch_feedback_btn.isChecked():
            self.tab1.scopeWidget.emitData.disconnect()
            self.feedbackLoop.StoreData(data)
        if self.tab3.launch_feedback_test_btn.isChecked():

            self.tab1.scopeWidget.emitData.disconnect()
            self.feedbackLoop.StoreData(data)
            print("feedback data stored")
        # send data to graphs
        self.DisplayAndStabilize(data)
     
    
    def StartStopScan(self, scanOn):
        if scanOn:
            print("scanon")
            if self.CheckDataFolderExistance() == "Proceed":
                print("data folder exists")
                # block interaction with the controls
                self.tab1.scanWidget.startScanPushButton.setText("Stop Scan") 
                self.tab1.scanWidget.scanGroupBox.setEnabled(False)
                self.tab1.scopeWidget.setEnabled(False)
                self.tab1.stageWidget.setEnabled(False)
                # Reinitialize the matshow display
                #self.TwoDPlotDraw([[0,0],[0,0]])
                # stop the scope trigger and clear the scope memory
                #self.scopeWidget.triggerModeComboBox.setCurrentIndex(3)
                self.tab1.scopeWidget.ClearSweeps()
                # create a scanning loop
                self.scanningLoop = ScanningLoop(self.tab1.scanWidget.centralPosSpinBox.value(),
                                                 self.tab1.scanWidget.stepSizeSpinBox.value(),
                                                 self.tab1.stageWidget.PositionNmLCD.intValue(),
                                                 self.tab1.scanWidget.nbrPointsSpinBox.value(),
                                                 self.tab1.scanWidget.mvtTypeComboBox.currentText(),
                                                 self.tab1.scanWidget.dataFolderEdit.text())
                # create and start the scanning thread
                self.scanningThread = QtCore.QThread()
                self.scanningLoop.moveToThread(self.scanningThread)
                self.ConnectScanSignals()
                self.scanningThread.start()
    
        else:
            reply = QtWidgets.QMessageBox.question(self, 'Message', "Do you want to stop the scan?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.scanningLoop.Stop()
                print("After scanningLoop.Stop")
                #self.EndOfScan()
                #print("After EndOfScan")
    
    def EndOfScan(self):
        print("EndOfScan")
        scanStatus = self.DisconnectScanSignals()

        if scanStatus != "Cancel scan":
            
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.tab1.scanWidget.startScanPushButton.blockSignals(True)
            
            self.tab1.scanWidget.startScanPushButton.setChecked(False)
            
            self.tab1.scanWidget.startScanPushButton.blockSignals(False)
            
            self.scanningThread.exit()
            print("2. exit scanningThread")           
            
            #generates bug
            
            #wait for the thread exit before going on :
            while self.scanningThread.isRunning():
                self.thread().msleep(500)
                print("3. Wait for thread to exit")
  
        #reenable the user inteface
        
        self.tab1.scanWidget.startScanPushButton.setText("Start Scan")
        
        self.tab1.scanWidget.scanGroupBox.setEnabled(True)
        self.tab1.scopeWidget.setEnabled(True)
        self.tab1.stageWidget.setEnabled(True)
        print("4. reenables buttons") 
        
        
    def ConnectScanSignals(self):
        self.scanningLoop.requestMotion.connect(lambda x : self.tab1.stageWidget.PositionNmSpinBox.setValue(self.tab1.stageWidget.PositionNmSpinBox.value() + x))
        self.tab1.stageWidget.smarActReader.motionEnded.connect(self.scanningLoop.smarActStopCondition.wakeAll)
        
        # Allow the scanningLoop to set the scope trigger mode
        #self.scanningLoop.setScopeMode.connect(self.scopeWidget.triggerModeComboBox.setCurrentIndex)
        # Allow the scanningLoop to clear the scope memory after motion :
        self.scanningLoop.requestScopeMemoryClear.connect(self.tab1.scopeWidget.ClearSweeps)
        # connect the scanning loop Run function to the scanning thread start
        self.scanningThread.started.connect(self.scanningLoop.Run)
        # connect the scanningLoop 
        self.scanningLoop.requestEmitDataReconnection.connect(self.ConnectDisplay)
        #self.tab3.feedbackLoop.requestEmitDataReconnection.connect(self.ConnectDisplay)        
        # ... and wait for the end of the scan :
        self.scanningLoop.scanFinished.connect(self.EndOfScan)
    
    
    def ConnectDisplay(self):
        print('connect display')
        self.tab1.scopeWidget.emitData.connect(self.ForwardData)
        #print('')
        
    def DisconnectScanSignals(self):
        self.scanningLoop.requestMotion.disconnect()
        self.tab1.stageWidget.smarActReader.motionEnded.disconnect()
        self.scanningLoop.requestScopeMemoryClear.disconnect()
        self.scanningThread.started.disconnect()
        self.scanningLoop.scanFinished.disconnect()
        self.ConnectDisplay()
        
        
        
    
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Do you really want to close the program?", QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
    
        if reply == QtWidgets.QMessageBox.Yes:
            # exit scope
            self.tab1.scopeWidget.quitScope()
            # exit smarAct
            if self.tab1.stageWidget.ChannelComboBox.currentIndex() != 0:
                self.tab1.stageWidget.ChannelComboBox.setCurrentIndex(0)
            if self.tab1.stageWidget.ControlerComboBox.currentIndex() != 0:
                self.tab1.stageWidget.ControlerComboBox.setCurrentIndex(0)
            event.accept()
            QtCore.QCoreApplication.instance().quit
        else:
            event.ignore()      
     







    ################################ feedback #############################
    
    
    
    def ActivateDeactivateFeedback(self):
        # enable/diable the "start scan" button ont he scan widget depending on the other widgets states 
        scopeOn = self.tab1.scopeWidget.scopeGroupBox.isChecked()
        stageOn = self.tab1.stageWidget.ChannelComboBox.currentIndex()>0
        if scopeOn and stageOn:
            self.tab3.launch_feedback_btn.setEnabled(True)
            self.tab3.launch_feedback_test_btn.setEnabled(True)
            #self.scanWidget.scanGroupBox.setEnabled(True)
        else:
            self.tab3.launch_feedback_test_btn.setEnabled(False)
            #self.scanWidget.scanGroupBox.setEnabled(False)
    
    def CheckDataFolderExsitance(self):
        folderName = self.tab3.storedatafolder_display.text()
        if not os.path.exists(folderName):
            reply = QtWidgets.QMessageBox.question(self, "Message",
                                                   "The specified data folder does NOT exist. Do you want to create it?", QtWidgets.QMessageBox.Yes | 
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                os.makedirs(folderName)
            else:
                return "Cancel feedback"
        return "Proceed"
    
    
    ################## ForwardData in Rabbit_feedback_main


    def StartStopFeedback(self, feedbackStatus, mode):
        print("STARTSTOPFEEDBACK")
        
        if feedbackStatus:
            self.CheckDataFolderExsitance()
            # block interaction with the controls
            if mode == "Feedback":
                self.tab3.launch_feedback_btn.setText("STOP RABBIT \n FEEDBACK")
            if mode == "Test Feedback":
                self.tab3.launch_feedback_test_btn.setText("STOP RABBIT \n FEEDBACK TEST")
            self.tab2.setEnabled(False)
            self.tab1.scopeWidget.setEnabled(False)
            self.tab1.stageWidget.setEnabled(False)
            # Reinitialize the matshow display
            # stop the scope trigger and clear the scope memory
            #self.scopeWidget.triggerModeComboBox.setCurrentIndex(3)
            self.tab1.scopeWidget.ClearSweeps()
            # create a scanning loop
            self.tab3.SBParam = [self.tab2.O1, self.tab2.O2,  self.tab2.A1, self.tab2.A1, self.tab2.phi1, self.tab2.phi2]
            self.tab3.a = self.tab2.param_lin[0]/self.tab2.scan_step
            
            self.tab3.Kp = float(self.tab3.Kp_display.text())
            self.tab3.Ki = float(self.tab3.Ki_display.text())
            self.tab3.Kd = float(self.tab3.Kd_display.text())
        
        
            self.tab3.PIDParam = [self.tab3.Kp, self.tab3.Ki, self.tab3.Kd, self.tab3.T]
            
            # parameters: mode, tab3, lockingPos, SB_vector_int, BG_vector_int, SBParam, a, maxError, PIDParam, folder, tMax, feedbackNbr, errorValue
            self.feedbackLoop  = FeedbackLoop(mode, 
                                             self.tab3, 
                                             self.tab1.stageWidget.PositionNmLCD.intValue(),
                                             float(self.tab3.locking_position_display.text()),
                                             self.tab2.SB_vector_int,
                                             self.tab2.BG_vector_int,
                                             self.tab3.SBParam,
                                             self.tab3.a,
                                             float(self.tab3.max_error_display.text()),
                                             self.tab3.PIDParam,
                                             self.tab3.storedatafolder,
                                             self.tab3.tMax,
                                             self.tab3.feedbackNbr,
                                             self.tab3.errorValue)

            # create and start the scanning thread
            self.feedbackThread = QtCore.QThread()
            self.feedbackLoop.moveToThread(self.feedbackThread)
            self.ConnectFeedbackSignals()
            print("feedback thread start")
            self.feedbackThread.start()

        else:
            reply = QtWidgets.QMessageBox.question(self, 'Message', "Do you want to stop the feedback?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.feedbackLoop.Stop()
                print("after stop feedback loop")
                #self.EndOfFeedback()


    def EndOfFeedback(self):
        feedbackStatus = self.DisconnectFeedbackSignals()
        if feedbackStatus != "Cancel feedback":
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.tab3.launch_feedback_btn.blockSignals(True)
            self.tab3.launch_feedback_btn.setChecked(False)
            self.tab3.launch_feedback_btn.blockSignals(False)
            
            self.tab3.launch_feedback_test_btn.blockSignals(True)
            self.tab3.launch_feedback_test_btn.setChecked(False)
            self.tab3.launch_feedback_test_btn.blockSignals(False)
            
            
            self.feedbackThread.exit()
            print("exit feedbackThread")
            # wait for the thread exit before going on :
            
            while self.feedbackThread.isRunning():
                print("waiting 2")
                self.thread().msleep(100)
                
        
        #reenable the user inteface
        self.tab3.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
        self.tab3.launch_feedback_test_btn.setText("LAUNCH RABBIT \n FEEDBACK TEST")
        #self.scanWidget.scanGroupBox.setEnabled(True)
        self.tab1.scopeWidget.setEnabled(True)
        self.tab1.stageWidget.setEnabled(True)
        self.tab3.feedbackNbr += 1
        
        # for stabilized scan: send signal when the feedback is over
        
        self.tab3.stepOfStabScanFinished.emit()
        print("stepOfStabScanFinished emitted")


    def ConnectFeedbackSignals(self):
        self.feedbackLoop.requestFeedbackMotion.connect(lambda x : self.tab1.stageWidget.PositionNmSpinBox.setValue(int(self.tab1.stageWidget.PositionNmLCD.value() + x)))
        self.tab1.stageWidget.smarActReader.motionEnded.connect(self.feedbackLoop.smarActStopCondition.wakeAll)
        # Allow the scanningLoop to set the scope trigger mode
        #self.scanningLoop.setScopeMode.connect(self.scopeWidget.triggerModeComboBox.setCurrentIndex)
        # Allow the scanningLoop to clear the scope memory after motion :
        self.feedbackLoop.requestScopeMemoryClear.connect(self.tab1.scopeWidget.ClearSweeps)
        # connect the scanning loop Run function to the scanning thread start
        self.feedbackThread.started.connect(self.feedbackLoop.Run)
        # connect the scanningLoop 
        self.feedbackLoop.requestEmitDataReconnection.connect(self.ConnectDisplay)
        # ... and wait for the end of the scan :
        self.feedbackLoop.feedbackFinished.connect(self.EndOfFeedback)



    def DisconnectFeedbackSignals(self):
        print("disconnect feedback signals")
        self.feedbackLoop.requestFeedbackMotion.disconnect()
        self.tab1.stageWidget.smarActReader.motionEnded.disconnect()
        self.feedbackLoop.requestScopeMemoryClear.disconnect()
        self.feedbackThread.started.disconnect()
        self.feedbackLoop.feedbackFinished.disconnect()
        self.ConnectDisplay()






     
def main():
   
   app = QtWidgets.QApplication(sys.argv)
   app.aboutToQuit.connect(app.deleteLater)
   app.setStyle('Fusion')
   ex = RABBIT_feedback()
   ex.show()
   
   sys.exit(app.exec_())
   #sys.exit()
   #raise Exception('exit')
   #sys.exit(0)
   #app.quit()
	
if __name__ == '__main__':
   main()
  
    
   