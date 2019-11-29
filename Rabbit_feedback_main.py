"""The program has to be runned here"""





import sys
import os

import time

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon


#homemade modules
import live_win 
import sidebands_win
import feedback_win
import scanStab_win
from Rabbit_scan import ScanningLoop




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
        self.tab3 = feedback_win.FeedbackTab(self.tab1, self.tab2)
        #self.tab4 = scanStab_win.scanStabTab(self.tab3)
        
        self.addTab(self.tab1,"Live")
        self.addTab(self.tab2, "Sidebands")
        self.addTab(self.tab3, "Feedback")
        #self.addTab(self.tab4, "Stab scan")
        
        self.setWindowTitle("RABBIT Active Stabilization")
        self.setWindowIcon(QIcon("icon_sirius.png") )
        
        self.setGeometry(100, 100, 1510, 1000)
        
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()
        
        self.canMove = False
        

        
        self.period = 0.1 #s, period of the feedback loop
        
        self.tab3.T = self.period #ins, period in the PID controller       
        
        
        
        self.tGlob = 0
        
        # prepare the transmission of the data to the graphs (will also be used by the scanning loop)
        self.ConnectDisplay()
        # activate/deactivate widgets controls in agreement with the current configuation :
        # 1) Alow scan control if both scope and stage are running :
        self.tab1.scopeWidget.scopeGroupBox.toggled.connect(self.ActivateDeactivateScan)
        self.tab1.stageWidget.ChannelComboBox.currentIndexChanged.connect(self.ActivateDeactivateScan)
        # 2) disable controls duing the scan : 
        self.tab1.scanWidget.startScanPushButton.clicked.connect(self.StartStopScan)
        
        
        self.show()
        
    #################################################################################################    
    ################################## RABBIT FEEDBACK FUNCTIONS ############################################
        
        
    def DisplayAndStabilize(self, data):  #updates the scope windows (scope 1, scope 2, time error plot and time delay position) and performs feedback
        scale_y = self.tab1.scopeWidget.YScale
        scale_x = self.tab1.scopeWidget.XScale
        y_offset = self.tab1.scopeWidget.YOffset
        x_offset = self.tab1.scopeWidget.XOffset

        ########### updates scope screen in tab 1 ################
        self.tab1.updateLiveScreen(data, scale_x, scale_y, x_offset, y_offset)
        
        ########### updates screens in tab 3 ################

        if self.tGlob%6 == 0: #☻doesnt update all the time during feedback
            self.tab3.updateFeedbackScreens(data, scale_x, scale_y, x_offset, y_offset)
            print("")
            print("DISPLAY")
            print("")
            
            
        ################## performs feedback #################
        
        self.tab3.ForwardFeedback(data)

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
        if self.tab1.scanWidget.startScanPushButton.isChecked():
            # during a scan : transmit the data to the scanningLoop object and disable the conection to prevent multiple acquisition at a single delay
            self.tab1.scopeWidget.emitData.disconnect()
            self.scanningLoop.StoreData(data)
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
                self.EndOfScan()
                print("After EndOfScan")
    
    def EndOfScan(self):
        scanStatus = self.DisconnectScanSignals()
        
        if scanStatus != "Cancel scan":
            
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.tab1.scanWidget.startScanPushButton.blockSignals(True)
            
            self.tab1.scanWidget.startScanPushButton.setChecked(False)
            
            self.tab1.scanWidget.startScanPushButton.blockSignals(False)
            
            self.scanningThread.exit()
            
            
            #generates bug
            '''
            # wait for the thread exit before going on :
            while self.scanningThread.isRunning():
                self.thread().msleep(100)
            '''
            
        #reenable the user inteface
        
        self.tab1.scanWidget.startScanPushButton.setText("Start Scan")
        
        self.tab1.scanWidget.scanGroupBox.setEnabled(True)
        self.tab1.scopeWidget.setEnabled(True)
        self.tab1.stageWidget.setEnabled(True)
    
    
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
        # ... and wait for the end of the scan :
        self.scanningLoop.scanFinished.connect(self.EndOfScan)
    
    
    def ConnectDisplay(self):
        print('a')
        self.tab1.scopeWidget.emitData.connect(self.ForwardData)
        print('b')
        
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
 
    '''           
    def allowMove(self):
        #print("allow move")
        self.tab1.scopeWidget.reader.canAsk = True
        #print("canAsk set to TRUE")
        self.canMove = True
        '''
        
     
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
  
    
   