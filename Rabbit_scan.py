# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 14:26:17 2019

@author: mluttmann
"""

"""
Complete integratio of the smaract delay line and the Lecoy waverunner oscilloscope in the RABBIT
"""

from SmarAct_f import StageWidget
import sys
import os

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QIcon

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


# TODO :
# 1) the scanning loop does NOT stop when quitting the application !!!!!
# 2) add a moveAbolute signal to the ScanningLoop to send the smarAct to the start position ???

"""
class handling the scan operations
"""
class ScanningLoop(QtCore.QObject):
    scanFinished = QtCore.pyqtSignal()
    requestMotion = QtCore.pyqtSignal(int)
    requestScopeMemoryClear = QtCore.pyqtSignal()
    setScopeMode = QtCore.pyqtSignal(int)
    requestEmitDataReconnection = QtCore.pyqtSignal()
    def __init__(self, middle, step, currentPos, nbrOfPoints, direction, folder):
        super(ScanningLoop, self).__init__()
        self.nbrOfPoints = nbrOfPoints
        self.step = int(step)
        if direction == "Backward":
            self.step = -self.step
        
        self.start = middle - (self.step*self.nbrOfPoints)/2
        self.moveTo = self.start-currentPos
        self.folder = folder
        self.data = []
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()

        # start the scanning loop
        self.run = True

    def Run(self):
        # move to the intial position and wait until initial position is reached
        print("begin Run")
        self.mutex.lock()
        #print("after mutex lock")
        self.requestMotion.emit(self.moveTo)
        #print("after request motion")
        self.smarActStopCondition.wait(self.mutex)
        #print("after smaractstopcondition wait")
        self.mutex.unlock()
        #print("after unlock mutex")
        for ii in range(self.nbrOfPoints):
#            # clear scope memory
#            print('clear memory')
#            self.requestScopeMemoryClear.emit()
            
            # freeze this loop while the stage is not at destination :
            
            if not self.run:
                print("BREAK LOOP")
                break
                
            print("")
            print('start scan step')
            self.mutex.lock()
            #print("loop")
            self.requestMotion.emit(self.step)
            self.smarActStopCondition.wait(self.mutex)
            #print("after .wait in scan")
            self.mutex.unlock()
            
            # allow data emition fro mthe scopeWidget
            self.requestEmitDataReconnection.emit()
            # trigger scope
            self.setScopeMode.emit(0)
            
            # read scope
            
            while self.data == []:
                self.thread().msleep(100)
                print('Waiting data')
                if not self.run:
                    print("BREAK LOOP data")
                    break

            self.requestScopeMemoryClear.emit()
            
            
            if self.run:
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
            if not self.run:
                print("BREAK LOOP")
                break            
                '''
        self.scanFinished.emit()
        print("LOOP OUT")
        
    def StoreData(self, data):
        self.data = data
        if data != []:
            # stop the scope while the main loop write the data in a file
            self.setScopeMode.emit(3)

        
    def Stop(self):
        print("1. Stop scanning loop")
        self.run = False
            


"""
Scan Widet class
"""
qtCreatorFile = "ScanPyQt5UI.ui"
Ui_StopScanWidget, QtBaseClass = loadUiType(qtCreatorFile)
class ScanWidget(QtWidgets.QFrame, Ui_StopScanWidget):
    def __init__(self, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setupUi(self)



"""
Rabbit Window class
"""
class RabbitMainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.scopeWidget = ScopeWidget()
        self.stageWidget = StageWidget()
        # create an empty widget used as a cenrtal widget for the qmainwindow and a container for other widgets :
        self.centralWidget = QtWidgets.QWidget()
        # create the central widget layout :
        self.mainLayout = QtWidgets.QHBoxLayout()
        # it is sepaaed in two parts with he controls on the left :
        self.leftLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self.leftLayout)
        self.leftLayout.addWidget(self.scopeWidget) # fist the scope controls
        self.leftLayout.addWidget(self.stageWidget) # second the delay lins controls
        # and last the scan controls :
        self.scanWidget = ScanWidget()
        
        self.scanWidget.dataFolderEdit.editingFinished.connect(self.CheckDataFolderExsitance)
        self.leftLayout.addWidget(self.scanWidget)

        # create tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()	
        self.tab2 = QtWidgets.QWidget()
        # setup tabs
        self.mainLayout.addWidget(self.tabs)
        self.tabs.addTab(self.tab1,"Scope Tab")
        self.tabs.addTab(self.tab2,"2D Plot Tab")


        # Raw scope data plot :
        # create a figure and a figure navigation tool on a layout
        self.scopePlotLayout = QtWidgets.QVBoxLayout()
        # create the figure and the figure navigation
        self.scopePlotFigure = plt.Figure()
        self.scopePlotAxis = self.scopePlotFigure.add_subplot(111, facecolor='k')
#            self.axis.axis('auto')
        self.scopePlotCanvas = FigureCanvas(self.scopePlotFigure)             # Canvas Widget that displays the figure
        self.scopePlotCanvas.setMinimumWidth(250)
        self.scopePlotCanvas.setMinimumHeight(250)
        
        self.scopePlotTrace, = self.scopePlotAxis.plot([0,1],[0,0],color='yellow')
        self.toolbar = NavigationToolbar(self.scopePlotCanvas, self) # Navigation widget
        # add the figure and the figure navigation to the figure layout
        self.scopePlotLayout.addWidget(self.toolbar)
        self.scopePlotLayout.addWidget(self.scopePlotCanvas)
        # add the figure layout to the main layout
        self.tab1.setLayout(self.scopePlotLayout)

        # data plot for the 2D accumulation of scans :
        # create a figure and a figure navigation tool on a layout
        self.TwoDPlotLayout = QtWidgets.QVBoxLayout()
        # create the figure and the figure navigation
        self.TwoDPlotFigure = plt.Figure()
        self.TwoDPlotAxis = self.TwoDPlotFigure.add_subplot(111)
#            self.axis.axis('auto')
        self.TwoDPlotCanvas = FigureCanvas(self.TwoDPlotFigure)             # Canvas Widget that displays the figure
        self.TwoDPlotCanvas.setMinimumWidth(250)
        self.TwoDPlotCanvas.setMinimumHeight(250)
        self.TwoDPlotTrace = self.TwoDPlotAxis.matshow([[0,0],[0,0.01]])
        self.TwoDToolbar = NavigationToolbar(self.TwoDPlotCanvas, self) # Navigation widget
        # add the figure and the figure navigation to the figure layout
        self.TwoDPlotLayout.addWidget(self.TwoDToolbar)
        self.TwoDPlotLayout.addWidget(self.TwoDPlotCanvas)
        # add the figure layout to the main layout
        self.tab2.setLayout(self.TwoDPlotLayout)

        self.centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.centralWidget)

        self.setGeometry(100, 100, 980, 540)
#            self.setFixedSize(340, 270)
        self.setWindowTitle('Scope Control Widget')
        self.setWindowIcon(QIcon('web.png'))


        """
        main window creationand design
        """
        # setup menu bar
        self.statusBar()
        self.menuBar = self.menuBar()
        self.applicationMenu = self.menuBar.addMenu('Application')
        # create a quit action
        self.quitAction = QtWidgets.QAction('Quit', self)
        self.quitAction.setShortcut('Ctrl+Q')
        self.quitAction.setStatusTip('Exit application')
        self.quitAction.triggered.connect(self.close)
        # Add actions to the menubar
        self.applicationMenu.addAction(self.quitAction)

        # prepare the transmission of the data to the graphs (will also be used by the scanning loop)
        self.ConnectDisplay()
        # activate/deactivate widgets controls in agreement with the current configuation :
        # 1) Alow scan control if both scope and stage are running :
        self.scopeWidget.scopeGroupBox.toggled.connect(self.ActivateDeactivateScan)
        self.stageWidget.ChannelComboBox.currentIndexChanged.connect(self.ActivateDeactivateScan)
         # 2) disable controls duing the scan : 
        self.scanWidget.startScanPushButton.clicked.connect(self.StartStopScan)
        
    def ScopePlotDraw(self, data):
        
        
        scale_y=self.scopeWidget.YScale
        scale_x=self.scopeWidget.XScale
        offset=self.scopeWidget.YOffset
        
        data_y=[]
        for i in range(len(data[1])):
            data_y.append(data[1][i]-offset)
        self.scopePlotTrace.set_xdata(data[0])
        self.scopePlotTrace.set_ydata(data_y)
        self.scopePlotAxis.set_xlim([-5*scale_x, 5*scale_x])
        self.scopePlotAxis.set_ylim([-4*scale_y, 4*scale_y])
        self.scopePlotAxis.grid(True)
        self.scopePlotAxis.set_ylabel("Tension (V)", fontsize=20)
        self.scopePlotAxis.set_xlabel("Time (s)", fontsize=20)
        self.scopePlotCanvas.draw()

    def TwoDPlotDraw(self, data):
        oldData = self.TwoDPlotTrace.get_array()
        data = np.array(data).T
        data = np.expand_dims(data[:,1], axis=1)
        if data.shape[0] != oldData.shape[0]:
            self.TwoDPlotTrace.set_array(data)
            
            self.TwoDPlotTrace.set_extent([0, 1, 0, data.shape[0]])
#                self.TwoDPlotAxis.set_xlim([0,data.shape[0]])
#                self.TwoDPlotAxis.set_ylim([0,data.shape[0]])
            self.TwoDPlotAxis.set_aspect('auto')
            self.TwoDPlotTrace.set_clim(vmin=data.min(), vmax=data.max())
        else:
            data = np.hstack((oldData, data))
            self.TwoDPlotTrace.set_array(data)
            self.TwoDPlotTrace.set_extent([0, data.shape[1], 0, data.shape[0]])

        self.TwoDPlotCanvas.draw()

    def ActivateDeactivateScan(self):
        # enable/diable the "start scan" button ont he scan widget depending on the other widgets states 
        scopeOn = self.scopeWidget.scopeGroupBox.isChecked()
        stageOn = self.stageWidget.ChannelComboBox.currentIndex()>0
        if scopeOn and stageOn:
            self.scanWidget.startScanPushButton.setEnabled(True)
            self.scanWidget.scanGroupBox.setEnabled(True)
        else:
            self.scanWidget.startScanPushButton.setEnabled(False)
            self.scanWidget.scanGroupBox.setEnabled(False)
    
    def CheckDataFolderExsitance(self):
        folderName = self.scanWidget.dataFolderEdit.text()
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
        if self.scanWidget.startScanPushButton.isChecked():
            # during a scan : transmit the data to the scanningLoop object and disable the conection to prevent multiple acquisition at a single delay
            self.scopeWidget.emitData.disconnect()
            self.scanningLoop.StoreData(data)
        # send data to graphs
        self.ScopePlotDraw(data)
        self.TwoDPlotDraw(data)

    def StartStopScan(self, scanOn):
        
        if scanOn:
            self.CheckDataFolderExsitance()
            # block interaction with the controls
            self.scanWidget.startScanPushButton.setText("Stop Scan")
            self.scanWidget.scanGroupBox.setEnabled(False)
            self.scopeWidget.setEnabled(False)
            self.stageWidget.setEnabled(False)
            # Reinitialize the matshow display
            self.TwoDPlotDraw([[0,0],[0,0]])
            # stop the scope trigger and clear the scope memory
            #self.scopeWidget.triggerModeComboBox.setCurrentIndex(3)
            self.scopeWidget.ClearSweeps()
            # create a scanning loop
            self.scanningLoop  = ScanningLoop(self.scanWidget.centralPosSpinBox.value(),
                                             self.scanWidget.stepSizeSpinBox.value(),
                                             self.stageWidget.PositionNmLCD.intValue(),
                                             self.scanWidget.nbrPointsSpinBox.value(),
                                             self.scanWidget.mvtTypeComboBox.currentText(),
                                             self.scanWidget.dataFolderEdit.text())
            # create and start the scanning thread
            self.scanningThread = QtCore.QThread()
            self.scanningLoop.moveToThread(self.scanningThread)
            self.ConnectScanSignals()
            print("thread start")
            self.scanningThread.start()

        else:
            reply = QtWidgets.QMessageBox.question(self, 'Message', "Do you want to stop the scan?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.scanningLoop.Stop()
                self.EndOfScan()


    def EndOfScan(self):
        scanStatus = self.DisconnectScanSignals()
        if scanStatus != "Cancel scan":
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.scanWidget.startScanPushButton.blockSignals(True)
            self.scanWidget.startScanPushButton.setChecked(False)
            self.scanWidget.startScanPushButton.blockSignals(False)
            
            self.scanningThread.exit()
            print("2. exit scanningThread")
            # wait for the thread exit before going on :
            while self.scanningThread.isRunning():
                self.thread().msleep(100)
                print("3. Wait for thread to exit")
        #reenable the user inteface
        self.scanWidget.startScanPushButton.setText("Start Scan")
        self.scanWidget.scanGroupBox.setEnabled(True)
        self.scopeWidget.setEnabled(True)
        self.stageWidget.setEnabled(True)
        print("4. reenables buttons")

    def ConnectScanSignals(self):
        self.scanningLoop.requestMotion.connect(lambda x : self.stageWidget.PositionNmSpinBox.setValue(self.stageWidget.PositionNmSpinBox.value() + x))
        self.stageWidget.smarActReader.motionEnded.connect(self.scanningLoop.smarActStopCondition.wakeAll)
        # Allow the scanningLoop to set the scope trigger mode
        #self.scanningLoop.setScopeMode.connect(self.scopeWidget.triggerModeComboBox.setCurrentIndex)
        # Allow the scanningLoop to clear the scope memory after motion :
        self.scanningLoop.requestScopeMemoryClear.connect(self.scopeWidget.ClearSweeps)
        # connect the scanning loop Run function to the scanning thread start
        self.scanningThread.started.connect(self.scanningLoop.Run)
        # connect the scanningLoop 
        self.scanningLoop.requestEmitDataReconnection.connect(self.ConnectDisplay)
        # ... and wait for the end of the scan :
        self.scanningLoop.scanFinished.connect(self.EndOfScan)


    def ConnectDisplay(self):
        print('a')
        self.scopeWidget.emitData.connect(self.ForwardData)
        print('b')
        
    def DisconnectScanSignals(self):
        self.scanningLoop.requestMotion.disconnect()
        self.stageWidget.smarActReader.motionEnded.disconnect()
        self.scanningLoop.requestScopeMemoryClear.disconnect()
        self.scanningThread.started.disconnect()
        self.scanningLoop.scanFinished.disconnect()
        self.ConnectDisplay()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            # exit scope
            self.scopeWidget.quitScope()
            # exit smarAct
            if self.stageWidget.ChannelComboBox.currentIndex() != 0:
                self.stageWidget.ChannelComboBox.setCurrentIndex(0)
            if self.stageWidget.ControlerComboBox.currentIndex() != 0:
                self.stageWidget.ControlerComboBox.setCurrentIndex(0)
            event.accept()
            QtCore.QCoreApplication.instance().quit
        else:
            event.ignore()            

if __name__ == '__main__':

    
    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater) # seems to allow a proper handling of the "close" event under the anaconda distribution
    rabbitMainWindow = RabbitMainWindow()
    rabbitMainWindow.show()
    sys.exit(app.exec_())
