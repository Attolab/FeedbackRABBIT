import sys
import os



import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QIcon, QFont
#from PyQt5.QtGui import QStyleFactory
#import PyQt5.QtWidgets as qtw
import traceback
from glob import glob

from Scope_f import ScopeWidget, ScopeReader
from SmarAct_f import StageWidget, SmarActReader
from Rabbit_scan import ScanWidget, ScanningLoop


import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar



class RABBIT_feedback(QtWidgets.QTabWidget):
    
    requestMotion = QtCore.pyqtSignal(int)
    
    def __init__(self, parent = None):
        super(RABBIT_feedback, self).__init__(parent)
    
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()
        self.tab3 = QtWidgets.QWidget()
      
        self.scopeWidget = ScopeWidget()
        self.stageWidget = StageWidget()
        self.scanWidget = ScanWidget()
        
        
        self.scopeWidget_feedback = ScopeWidget()
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()
        
        self.addTab(self.tab1,"Live")
        self.addTab(self.tab2,"Sidebands")
        self.addTab(self.tab3,"Feedback")
        
        
        ###### scan analysis #######
        
        
        self.omega = 2.35*10**(15)  #IR laser pulsation in rad/s
        self.c_m_s = 3*10**8  #speed of light
        self.scan_step = 20.
        self.rabbit_mat = None
        
        self.data_x = []
        self.SB_vector_int = []  #sidebands positions
        self.BG_vector = []   #background band vector
        
        self.int_SB1 = []
        self.int_SB2 = []
        
        self.int_offset = []
        
        self.retrieved_SB1 = []
        self.retrieved_SB2 = []
        
        self.fit_SB1 = []
        self.fit_SB2 = []

        self.O1 = 0.
        self.O2 = 0.
        self.A1 = 0.
        self.A2 = 0.
        self.dphi = 0.
        
        self.data_x_nm=[]
        self.list_error = []
        
        
        ###### feedback ######
        
        
        self.live_time_data = [0]
        self.live_error_data = [0]
        self.live_position_data = [0]
        
        self.Kp = 0.1
        self.Ti = 1.
        self.Td = 0.
        
        self.T = 1000  #scope refreshing period
        
        self.U = [0,0]
        self.E = [0,0,0]
        
        self.locking_position = 1000.
        
        self.max_move = 50  #(nm)
        
        self.x_error_nm = 0.
        
        self.feedbackStatus = False   #feedback not running yet
       
        self.LiveUI()
        self.SidebandsUI()
        self.FeedbackUI()
        self.setWindowTitle("RABBIT feedback")
        self.setWindowIcon(QIcon("lapin.png") )
      
        self.setGeometry(100, 100, 1500, 1000)
        self.show()
      
    		
        
    #####################################################Layout########################################################
		
    def LiveUI(self):
      
       
        # create the figure and the figure navigation
       self.scopePlotFigure = plt.Figure()
       self.scopePlotAxis = self.scopePlotFigure.add_subplot(111, facecolor='k')
       self.scopePlotCanvas = FigureCanvas(self.scopePlotFigure)          
       self.scopePlotCanvas.setMinimumWidth(250)
       self.scopePlotCanvas.setMinimumHeight(500)
       self.scopePlotCanvas.setMaximumWidth(1000)
       self.scopePlotCanvas.setMaximumHeight(700)
       
       self.scopePlotTrace, = self.scopePlotAxis.plot([0,1],[0,0],color='yellow')
       
       
       box = QtWidgets.QHBoxLayout()
       
       
       winLayout=QtWidgets.QVBoxLayout()
       winLayout.addWidget(self.scopeWidget)
       winLayout.addWidget(self.stageWidget)
       winLayout.addWidget(self.scanWidget)
       winLayout.setSpacing(120)
       #winLayout.addStretch(0)
       
       
       box.addLayout(winLayout)
       box.addWidget(self.scopePlotCanvas)
       
      
       self.tab1.setLayout(box)
       
       
       # prepare the transmission of the data to the graphs (will also be used by the scanning loop)
       self.ConnectDisplay()
       # activate/deactivate widgets controls in agreement with the current configuation :
       # 1) Alow scan control if both scope and stage are running :
       self.scopeWidget.scopeGroupBox.toggled.connect(self.ActivateDeactivateScan)
       self.stageWidget.ChannelComboBox.currentIndexChanged.connect(self.ActivateDeactivateScan)
       # 2) disable controls duing the scan : 
       self.scanWidget.startScanPushButton.clicked.connect(self.StartStopScan)
       
       
		
    def SidebandsUI(self):
        self.scanPlotLayout = QtWidgets.QVBoxLayout()
        
        self.scanPlotFigure = plt.Figure()
        self.scanPlotAxis = self.scanPlotFigure.add_subplot(111)
        self.scanPlotCanvas = FigureCanvas(self.scanPlotFigure)             # Canvas Widget that displays the figure
        self.scanPlotCanvas.setMinimumWidth(700)
        self.scanPlotCanvas.setMinimumHeight(500)
        self.scanPlotTrace = self.scanPlotAxis.matshow([[0,0],[0,0]])
        self.scanPlotLayout.addWidget(self.scanPlotCanvas)
        
        self.step_display = QtWidgets.QLineEdit("{:.2f}".format(self.scan_step), self)
        self.step_display.setMaximumWidth(80)
        self.step_display.setText("20")
        
        
        self.n = 1
        self.SB_vector = []
        self.nbr_clicks = 0
        
        self.scan_step = 20.
        
        
        
        self.SBPlotLayout = QtWidgets.QVBoxLayout()
        self.SBPlotFigure = plt.Figure()
        self.SBPlotAxis = self.SBPlotFigure.add_subplot(111)
        self.SBPlotCanvas = FigureCanvas(self.SBPlotFigure)             
        self.SBPlotLayout.addWidget(self.SBPlotCanvas)
        self.SBPlotAxis.clear()
        
        
        self.horPlotLayout = QtWidgets.QVBoxLayout()
        self.horPlotFigure = plt.Figure()
        self.horPlotAxis = self.horPlotFigure.add_subplot(111)
        self.horPlotCanvas = FigureCanvas(self.horPlotFigure)             
        self.horPlotLayout.addWidget(self.horPlotCanvas)
        self.horPlotAxis.clear()
        
        
        self.errorPlotLayout = QtWidgets.QVBoxLayout()
        self.errorPlotFigure = plt.Figure()
        self.errorPlotAxis = self.errorPlotFigure.add_subplot(111)
        self.errorPlotCanvas = FigureCanvas(self.errorPlotFigure)             
        self.errorPlotLayout.addWidget(self.errorPlotCanvas)
        self.errorPlotAxis.clear()
        
        
        self.importdata_btn = QtWidgets.QPushButton("Load RABBIT scan", self)
        self.importdata_btn.clicked.connect(self.import_scan)
        self.importdata_btn.setMaximumWidth(150)
        
        
        self.SB_plot_btn = QtWidgets.QPushButton("Plot sidebands", self)
        self.SB_plot_btn.clicked.connect(self.SBPlotDraw)
        self.SB_plot_btn.setMaximumWidth(150)
        
        
        self.horizontal_plot_btn = QtWidgets.QPushButton("Plot horizontal cross-section", self)
        self.horizontal_plot_btn.clicked.connect(self.horPlotDraw)
        self.horizontal_plot_btn.setMaximumWidth(200)
        
        
        self.error_plot_btn = QtWidgets.QPushButton("Plot error signal", self)
        self.error_plot_btn.clicked.connect(self.errorPlotDraw)
        self.error_plot_btn.setMaximumWidth(200)
        
        
        self.O1_display = QtWidgets.QLineEdit("{:.2f}".format(self.O1), self)
        self.O2_display = QtWidgets.QLineEdit("{:.2f}".format(self.O2), self)
        self.A1_display = QtWidgets.QLineEdit("{:.2f}".format(self.A1), self)
        self.A2_display = QtWidgets.QLineEdit("{:.2f}".format(self.A2), self)
        self.dphi_display = QtWidgets.QLineEdit("{:.2f}".format(self.dphi), self)
        
        
        box2 = QtWidgets.QGridLayout()
        box2.setSpacing(10)
        
        small_layout=QtWidgets.QHBoxLayout()
        small_layout.addWidget(self.importdata_btn)
        small_layout.addWidget(QtWidgets.QLabel("Scan step (nm)"))
        small_layout.addWidget(self.step_display)
        small_layout.addStretch(10)
        #small_layout.setContentsMargins(100,300,100,300)
        small_layout.setSpacing(10)
       
        
        ########################
        
        scanLayout=QtWidgets.QGridLayout()
        scanLayout.addLayout(small_layout,0,0)
        
        scanLayout.addWidget(self.scanPlotCanvas,1,0)
        scanLayout.addWidget(self.horizontal_plot_btn,2,0)
        scanLayout.addWidget(self.horPlotCanvas,3,0)
        
        
        box2.addLayout(scanLayout,0,0)
        
        #########################
        
        signalLayout=QtWidgets.QGridLayout()
        signalLayout.addWidget(self.SB_plot_btn, 0, 0)
        signalLayout.addWidget(self.SBPlotCanvas, 1, 0)
        
        paramGroupBox = QtWidgets.QGroupBox(self)
        paramGroupBox.setTitle("Fit parameters")
        
        paramLayout = QtWidgets.QGridLayout()
        paramLayout.addWidget(QtWidgets.QLabel("Offset 1"),0,0)
        paramLayout.addWidget(self.O1_display,1,0)
        paramLayout.addWidget(QtWidgets.QLabel("Offset 2"),0,1)
        paramLayout.addWidget(self.O2_display,1,1)
        paramLayout.addWidget(QtWidgets.QLabel("Amplitude 1"),0,2)
        paramLayout.addWidget(self.A1_display,1,2)
        paramLayout.addWidget(QtWidgets.QLabel("Amplitude 2"),0,3)
        paramLayout.addWidget(self.A2_display,1,3)
        paramLayout.addWidget(QtWidgets.QLabel("Phase shift"),0,4)
        paramLayout.addWidget(self.dphi_display,1,4)
        
        paramGroupBox.setLayout(paramLayout)
        
        
        signalLayout.addWidget(paramGroupBox,2,0)
        signalLayout.addWidget(self.error_plot_btn, 3, 0)
        signalLayout.addWidget(self.errorPlotCanvas, 4, 0)
       
        box2.addLayout(signalLayout,0,1)
        
        self.tab2.setLayout(box2)
        
        
        
    def FeedbackUI(self):
        
        
        self.scope2PlotFigure = plt.Figure()
        self.scope2PlotAxis = self.scope2PlotFigure.add_subplot(111, facecolor='k')
        self.scope2PlotCanvas = FigureCanvas(self.scope2PlotFigure)          
        self.scope2PlotCanvas.setMinimumWidth(1000)
        self.scope2PlotCanvas.setMinimumHeight(500)
        self.scope2PlotCanvas.setMaximumWidth(1000)
        self.scope2PlotCanvas.setMaximumHeight(700)
       
        self.scope2PlotTrace, = self.scope2PlotAxis.plot([0,1],[0,0],color='yellow')
        
        
        
        
        self.time_errorPlotFigure = plt.Figure()
        self.time_errorPlotAxis = self.time_errorPlotFigure.add_subplot(111, facecolor='k')
        self.time_errorPlotCanvas = FigureCanvas(self.time_errorPlotFigure)          
        #self.time_errorPlotCanvas.setMinimumWidth(1000)
        #self.time_errorPlotCanvas.setMinimumHeight(100)
        self.time_errorPlotCanvas.setMaximumWidth(1000)
        self.time_errorPlotCanvas.setMaximumHeight(200)
       
        self.time_errorPlotTrace, = self.time_errorPlotAxis.plot([0,1],[0,0],color='yellow')
        
        
        self.time_positionPlotFigure = plt.Figure()
        self.time_positionPlotAxis = self.time_positionPlotFigure.add_subplot(111, facecolor='k')
        self.time_positionPlotCanvas = FigureCanvas(self.time_positionPlotFigure)          
        #self.time_positionPlotCanvas.setMinimumWidth(1000)
        #self.time_positionPlotCanvas.setMinimumHeight(100)
        self.time_positionPlotCanvas.setMaximumWidth(1000)
        self.time_positionPlotCanvas.setMaximumHeight(200)
       
        self.time_positionPlotTrace, = self.time_positionPlotAxis.plot([0,1],[0,0],color='yellow')
        
        
        self.Kp_display = QtWidgets.QLineEdit("{:.2f}".format(self.Kp), self)
        self.Kp_display.setMaximumWidth(80)
        self.Ti_display = QtWidgets.QLineEdit("{:.2f}".format(self.Ti), self)
        self.Ti_display.setMaximumWidth(80)
        self.Td_display = QtWidgets.QLineEdit("{:.2f}".format(self.Td), self)
        self.Td_display.setMaximumWidth(80)
        
        self.locking_position_display = QtWidgets.QLineEdit("{:.2f}".format(self.locking_position), self)
        self.locking_position_display.setMaximumWidth(80)
        
        self.max_move_display = QtWidgets.QLineEdit("{:.2f}".format(self.max_move), self)
        self.max_move_display.setMaximumWidth(80)
        
        self.launch_feedback_btn = QtWidgets.QPushButton("LAUNCH RABBIT \n FEEDBACK", self)
        self.launch_feedback_btn.setMaximumWidth(200)
        self.launch_feedback_btn.setCheckable(True)
        self.launch_feedback_btn.setIcon(QIcon('lapin.png'))
        self.launch_feedback_btn.setIconSize(QtCore.QSize(75,75))
        self.launch_feedback_btn.setFont(QFont('SansSerif', 10))
        
        self.launch_feedback_btn.clicked.connect(self.checkFeedback)
        
        ServoGroupBox = QtWidgets.QGroupBox(self)
        ServoGroupBox.setTitle("Servo parameters")
        
        
        GainLayout = QtWidgets.QGridLayout()
        GainLayout.addWidget(QtWidgets.QLabel("Kp"),0,0)
        GainLayout.addWidget(self.Kp_display,0,1)
        GainLayout.addWidget(QtWidgets.QLabel("Ti"),1,0)
        GainLayout.addWidget(self.Ti_display,1,1)
        GainLayout.addWidget(QtWidgets.QLabel("Td"),2,0)
        GainLayout.addWidget(self.Td_display,2,1)
        
        ServoGroupBox.setLayout(GainLayout)
        ServoGroupBox.setFixedWidth(125)
        
        #GainWidget = QtWidgets.QWidget()
        #GainWidget.setLayout(GainLayout)
        #GainWidget.setFixedWidth(125)
    
        lockingLayout = QtWidgets.QHBoxLayout()
        lockingLayout.addWidget(QtWidgets.QLabel("Locking position (nm)"))
        lockingLayout.addWidget(self.locking_position_display)
        
        
        maxLayout = QtWidgets.QHBoxLayout()
        maxLayout.addWidget(QtWidgets.QLabel("Max move (nm)"))
        maxLayout.addWidget(self.max_move_display)
        
        lockingWidget = QtWidgets.QWidget()
        lockingWidget.setLayout(lockingLayout)
        lockingWidget.setFixedWidth(205)
        
        maxWidget = QtWidgets.QWidget()
        maxWidget.setLayout(maxLayout)
        maxWidget.setFixedWidth(205)
        
        displayLayout = QtWidgets.QVBoxLayout()
        displayLayout.addWidget(self.scope2PlotCanvas)
        displayLayout.addWidget(self.time_errorPlotCanvas)
        displayLayout.addWidget(self.time_positionPlotCanvas)
        
        interactLayout = QtWidgets.QVBoxLayout()
        interactLayout.addWidget(ServoGroupBox)
        interactLayout.addWidget(lockingWidget)
        interactLayout.addWidget(maxWidget)
        interactLayout.addWidget(self.launch_feedback_btn)
        interactLayout.addStretch(10)
        interactLayout.setContentsMargins(100,300,100,300)
        interactLayout.setSpacing(0)
        
        
        box3 = QtWidgets.QHBoxLayout()
        box3.addLayout(displayLayout)
        box3.addLayout(interactLayout)
        
        self.tab3.setLayout(box3)
        
        
        #############################################################################functions###############################
      
        ################### Live-functions #################################
      
    def ScopePlotDraw(self, data):  #updates the scope windows (scope 1, scope 2, time error plot and time delay position) and performs feedback
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
       self.scopePlotAxis.set_ylabel("Tension (V)", fontsize=17)
       self.scopePlotAxis.set_xlabel("Time (s)", fontsize=17)
       
       self.scopePlotCanvas.draw()
       
       
       
       self.scope2PlotTrace.set_xdata(data[0])
       self.scope2PlotTrace.set_ydata(data_y)
       self.scope2PlotAxis.set_xlim([-5*scale_x, 5*scale_x])
       self.scope2PlotAxis.set_ylim([-4*scale_y, 4*scale_y])
       self.scope2PlotAxis.grid(True)
       self.scope2PlotAxis.set_ylabel("Tension (V)", fontsize=17)
       self.scope2PlotAxis.set_xlabel("Time (s)", fontsize=17)
       
       if len(self.SB_vector_int)==6:
           for i in range(6):
               self.scope2PlotAxis.axvline(x=self.SB_vector_int[i],color='yellow')
           
       
       
       self.scope2PlotCanvas.draw()
       
       
       
       
       
       self.time_errorPlotAxis.set_ylim([-100,100])
       self.time_positionPlotAxis.set_ylim([-100,100])
       

       
       le = len(self.live_time_data)
       if le<50:
           self.live_time_data.append(self.live_time_data[-1]+1)
           self.live_error_data.append(self.x_error_nm)
           self.live_position_data.append(self.stageWidget.PositionNmLCD.value())
           
       else:
           for i in range(le):
               self.live_time_data[i]+=1
           for i in range(le-1):
               self.live_error_data[i]=self.live_error_data[i+1]
               self.live_position_data[i]=self.live_position_data[i+1]
               
           self.live_error_data[-1]=self.x_error_nm
           self.live_position_data[-1]=self.stageWidget.PositionNmLCD.value()
           
           
           
           
       self.time_errorPlotTrace.set_xdata(self.live_time_data)
       self.time_errorPlotTrace.set_ydata(self.live_error_data)
       
       self.time_errorPlotAxis.set_xlim([self.live_time_data[0], self.live_time_data[-1]])
       self.time_errorPlotAxis.set_ylim([1.1*min(-max(self.live_error_data), min(self.live_error_data)), 1.1*max(max(self.live_error_data), -min(self.live_error_data))])
       
       self.time_errorPlotAxis.grid(True)
       self.time_errorPlotAxis.set_ylabel("Error (nm)", fontsize=7)
       self.time_errorPlotAxis.set_xlabel("Time (step)", fontsize=7)
       
       self.time_errorPlotCanvas.draw()
       
           
       
       
       
       self.time_positionPlotTrace.set_xdata(self.live_time_data)
       self.time_positionPlotTrace.set_ydata(self.live_position_data)
       self.time_positionPlotAxis.set_xlim([self.live_time_data[0], self.live_time_data[-1]])
       self.time_positionPlotAxis.set_ylim([1.1*min(-max(self.live_position_data), min(self.live_position_data)), 1.1*max(max(self.live_position_data), -min(self.live_position_data))])
       
       self.time_positionPlotAxis.grid(True)
       self.time_positionPlotAxis.set_ylabel("Delay line position (nm)", fontsize=7)
       self.time_positionPlotAxis.set_xlabel("Time (step)", fontsize=7)
       
       self.time_positionPlotCanvas.draw()
           
        ################## feedback #################
        #if self.launch_feedback_btn.isChecked():
       self.smarActReader = SmarActReader(self.stageWidget)
       self.smarActReader.newPosition.connect(self.stageWidget.displayNewPosition)
       self.checkFeedback()
       
       if self.feedbackStatus == True:
           
           self.tab2.setEnabled(False)
           #self.FeedbackStep(data, self.locking_position)
           self.FeedbackStepTest()
           self.launch_feedback_btn.setText("STOP RABBIT \n FEEDBACK ")
           self.launch_feedback_btn.setChecked(True)
            
           
       else:
           self.tab2.setEnabled(True)
           self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
           self.launch_feedback_btn.setChecked(False)
          
        
       
      
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
     
    
    def StartStopScan(self, scanOn):
        if scanOn:
            self.CheckDataFolderExsitance()
            # block interaction with the controls
            self.scanWidget.startScanPushButton.setText("Stop Scan")
            self.scanWidget.scanGroupBox.setEnabled(False)
            self.scopeWidget.setEnabled(False)
            self.stageWidget.setEnabled(False)
            # Reinitialize the matshow display
            #self.TwoDPlotDraw([[0,0],[0,0]])
            # stop the scope trigger and clear the scope memory
            #self.scopeWidget.triggerModeComboBox.setCurrentIndex(3)
            self.scopeWidget.ClearSweeps()
            # create a scanning loop
            self.scanningLoop = ScanningLoop(self.scanWidget.startPosSpinBox.value(),
                                             self.scanWidget.stopPosSpinBox.value(),
                                             self.stageWidget.PositionNmLCD.intValue(),
                                             self.scanWidget.nbrPointsSpinBox.value(),
                                             self.scanWidget.dataFolderEdit.text())
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
                self.EndOfScan()
    
    
    def EndOfScan(self):
        scanStatus = self.DisconnectScanSignals()
        if scanStatus != "Cancel scan":
            # Make sure that the startScanPushButton of the scanWidget return to the False state
            self.scanWidget.startScanPushButton.blockSignals(True)
            self.scanWidget.startScanPushButton.setChecked(False)
            self.scanWidget.startScanPushButton.blockSignals(False)
    
            self.scanningThread.exit()
            # wait for the thread exit before going on :
            while self.scanningThread.isRunning():
                self.thread().msleep(100)
        #reenable the user inteface
        self.scanWidget.startScanPushButton.setText("Start Scan")
        self.scanWidget.scanGroupBox.setEnabled(True)
        self.scopeWidget.setEnabled(True)
        self.stageWidget.setEnabled(True)
    
    
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
        #print('a')
        self.scopeWidget.emitData.connect(self.ForwardData)
        #print('b')
        
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
            
            
            
            
        ################### Sidebands-functions #################################
        
  
    
    
    
    def import_scan(self):
       
        data_f = QtWidgets.QFileDialog.getOpenFileName(self, 'Import RABBIT scan')
        data_filename = data_f[0]
        
        if (data_filename):
            fdir, fname = os.path.split(data_filename)
            fdir = fdir + '/'
            flist = glob(fdir + '*[0-9][0-9][0-9][0-9].txt')
            #flist contains the list of paths to all spectrum files
           
            self.n = len(flist)
           
            list_t = self.import_spectrum(flist[0])[0]
            n_t = len(list_t)
         
            RABBIT_array = np.zeros(shape=(self.n,n_t))
            
            for i in range(self.n):
                RABBIT_array[i] = self.import_spectrum(flist[i])[1]
           
            self.rabbit_mat = RABBIT_array
            '''
            for i in range(self.n):
                self.rabbit_mat[i]=self.rabbit_mat[i]/(self.rabbit_mat[i].sum())
              '''  
            self.rabbit_t = list_t
            
            self.scanPlotTrace = self.scanPlotAxis.matshow(self.rabbit_mat)
            self.scanPlotAxis.set_aspect('auto')
            self.scanPlotAxis.set_ylabel("Delay", fontsize=10)
            self.scanPlotAxis.set_xlabel("ToF", fontsize=10)
            self.scanPlotAxis.set_title("Select two sidebands (in red) in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
            
            
            self.scanPlotCanvas.draw()
            
            self.cid = self.scanPlotCanvas.mpl_connect('button_press_event', self)
            
      
    def __call__(self, event):
        
        if self.nbr_clicks<=6:
            """
            if self.nbr_clicks==6:
                self.SB_vector=[]
                self.nbr_clicks+=1
               
            else:
                """
            if self.nbr_clicks>=4:
                self.scanPlotAxis.axvline(x=event.xdata,color='black')
            
                #self.SB_vector.append(event.xdata)
                self.BG_vector.append(event.xdata)
                self.scanPlotCanvas.draw()
                self.scope2PlotCanvas.draw()
                self.nbr_clicks += 1
                
            else:
                self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
                    
                self.scanPlotAxis.axvline(x=event.xdata,color='red')
                #self.scope2PlotAxis.axvline(x=self.rabbit_t[int(event.xdata)],color='red')  #second view of the scope
                self.SB_vector.append(event.xdata)
                
                self.scanPlotCanvas.draw()
                
                self.scope2PlotCanvas.draw()
                self.nbr_clicks+=1
                self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
        if self.nbr_clicks>6:
            self.SB_vector = []
            self.BG_vector = []
            self.scanPlotAxis.clear()
            self.scanPlotTrace = self.scanPlotAxis.matshow(self.rabbit_mat)
            self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
            self.scanPlotAxis.set_aspect('auto')
            self.scanPlotAxis.set_ylabel("Delay (steps)", fontsize=16)
            self.scanPlotAxis.set_xlabel("ToF", fontsize=16)
            self.scanPlotCanvas.draw()
            self.nbr_clicks=0
        #print(self.SB_vector)
            
            #self.scope2PlotAxis.clear()
                
                
            
            
            

    def import_spectrum(self, filename):
        file = open(filename, 'r')
        data = []
        try:
            data = [[float(digit) for digit in line.split()] for line in file]
            '''
            if cts.decimal_separ == 'dot':
                data = [[float(digit) for digit in line.split()] for line in file]
            elif cts.decimal_separ == 'comma':
                data = [[float(digit.replace(',', '.')) for digit in line.split()] for line in file]
            else:
                print("Error in the code")'''
    
        except ValueError: #if the decimal separator is a comma
            data = [[float(digit.replace(',', '.')) for digit in line.split()] for line in file]
    
        except IndexError:
            print('Incorrect data file')
            #self.window().statusBar().showMessage('Incorrect data file')
    
        except Exception:
            print(traceback.format_exception(*sys.exc_info()))
    
        finally:
            data_array = np.asarray(data)  # converting 1D list into 2D array
        x_data = []
        y_data = []
        for elt in data_array:
            x_data.append(elt[0])
            y_data.append(elt[1])
    
    
        return [x_data,y_data]
        
       
    def cosine(self, x, O, A, phi):
        self.scan_step = float(self.step_display.text())
        tau_step = self.scan_step/(self.c_m_s*10**9)  #speed of light in nm/s
        #print(self.scan_step)
        
        w = self.omega*tau_step  #laser frequency with step units
        return O+A*np.cos(4*w*x+phi)
    
    def lin_fit(self, x, a, b):
        return a*x+b
    
    
    def SBPlotDraw(self):
        self.SBPlotAxis.clear()
        # first integrate
        
        self.int_SB1 = []
        self.int_SB2 = []
        
        self.fit_SB1 = []
        self.fit_SB2 = []
        
        self.SB_vector_int = []
        self.BG_vector_int = []
        
        self.retrieved_SB1 = []
        self.retrieved_SB2 = []
        self.int_offset = []
        
        for elt in self.SB_vector:
            self.SB_vector_int.append(int(elt))
        for elt in self.BG_vector:
            self.BG_vector_int.append(int(elt))
        self.SB_vector_int.sort()
        self.BG_vector_int.sort()
        for i in range(3):
            if i==0:  # first sideband
                int_left = self.SB_vector_int[0]
                int_right = self.SB_vector_int[1]
                width = int_right-int_left
                for i in range(self.n):
                    self.int_SB1.append(np.trapz(self.rabbit_mat[i][int_left:int_right])/width)
            if i==1:  #2nd sideband
                int_left = self.SB_vector_int[2]
                int_right = self.SB_vector_int[3]
                width = int_right-int_left
                for i in range(self.n):
                    self.int_SB2.append(np.trapz(self.rabbit_mat[i][int_left:int_right])/width)
                    
            if i==2:  #3rd sideband
                int_left = self.BG_vector_int[0]
                int_right = self.BG_vector_int[1]
                width = int_right-int_left
                for i in range(self.n):
                    integral=np.trapz(self.rabbit_mat[i][int_left:int_right])/width
                    self.retrieved_SB1.append(self.int_SB1[i]-integral)
                    self.retrieved_SB2.append(self.int_SB2[i]-integral)
                    self.int_offset.append(integral)
        
        
        self.data_x = np.linspace(0, self.n, self.n)
        
        # first fit
        params1, cov1 = optimize.curve_fit(self.cosine, self.data_x, self.retrieved_SB1)
        
        
        self.O1 = params1[0]
        self.A1 = params1[1]
        
        
        params2, cov2 = optimize.curve_fit(self.cosine, self.data_x, self.retrieved_SB2)
        self.O2 = params2[0]
        self.A2 = params2[1]
        
        self.dphi = params1[2]-params2[2]
        
        
        
        for i in range(self.n):
            self.fit_SB1.append(self.cosine(self.data_x[i], params1[0], params1[1], params1[2]))
            self.fit_SB2.append(self.cosine(self.data_x[i], params2[0], params2[1], params2[2]))
        
       
        # then plot
        
        #plot integrated sidebands 
        
        self.SBPlotAxis.plot(self.data_x, self.retrieved_SB1, label='SB1', linewidth=2)
        self.SBPlotAxis.plot(self.data_x, self.retrieved_SB2, label='SB2', linewidth=2)
        #self.SBPlotAxis.plot(self.data_x, self.int_offset, label='background')
        
        
        #plot fitted sidebands 
        self.SBPlotAxis.plot(self.data_x, self.cosine(self.data_x, params1[0], params1[1], params1[2]), label="Fit SB1")#, params1[3]))
        self.SBPlotAxis.plot(self.data_x, self.cosine(self.data_x, params2[0], params2[1], params2[2]), label="Fit SB2")#, params2[3]))
        self.SBPlotAxis.set_ylabel("Signal (V)", fontsize=10)
        self.SBPlotAxis.set_xlabel("Delay (steps)", fontsize=10)
        self.SBPlotAxis.set_title("Sidebands vs delay", fontsize=8)
        self.SBPlotAxis.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        self.SBPlotAxis.legend(loc='best')
        self.SBPlotCanvas.draw()
        
        
        self.O1_display.setText(str(round(self.O1,8)))
        self.O2_display.setText(str(round(self.O2,8)))
        self.A1_display.setText(str(round(self.A1,8)))
        self.A2_display.setText(str(round(self.A2,8)))
        self.dphi_display.setText(str(round(self.dphi,8)))
        
        
        
    def horPlotDraw(self):
        self.horPlotAxis.clear()
        self.horPlotAxis.plot(self.rabbit_mat[0])
        self.horPlotAxis.set_title("ToF signal at first step", fontsize=8)
        self.horPlotAxis.set_ylabel("Signal (V)", fontsize=10)
        self.horPlotAxis.set_xlabel("ToF", fontsize=10)
        self.horPlotAxis.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        self.horPlotCanvas.draw()
        

    def errorPlotDraw(self):
        
        self.errorPlotAxis.clear()
        self.list_error = []
        
        list_error_fit = []
        self.list_error = np.unwrap(np.arctan2(
            (self.retrieved_SB1 - self.O1)/self.A1,
            (self.retrieved_SB2 - self.O2)/self.A2
        ))
        list_error_fit = np.unwrap(np.arctan2(
            (self.fit_SB1 - self.O1)/self.A1,
            (self.fit_SB2 - self.O2)/self.A2
        ))
        
        param_lin, cov = optimize.curve_fit(self.lin_fit, self.data_x, self.list_error)
        
        self.data_x_nm=[]
        for elt in self.data_x:
            self.data_x_nm.append(elt*self.scan_step)
        
        
        self.errorPlotAxis.plot(self.data_x_nm, self.list_error, label= "Error signal")
        self.errorPlotAxis.plot(self.data_x_nm, list_error_fit, 'k--', label="Error signal extracted from cosine fit", )
        self.errorPlotAxis.plot(self.data_x_nm, self.lin_fit(self.data_x, param_lin[0], param_lin[1]), label= "Linear fit of the error signal")  
        self.errorPlotAxis.set_ylabel("Error signal", fontsize=10)
        self.errorPlotAxis.set_xlabel("Delay (nm)", fontsize=10)
        self.errorPlotAxis.legend(loc='best')
        self.errorPlotCanvas.draw()
    
    
    
    
        ################### Feedback-functions #################################
    
        
    
    def checkFeedback(self):  #gives the authorization for starting the stabilization
        
        if self.launch_feedback_btn.isChecked():
            if self.scopeWidget.scopeGroupBox.isChecked():
                if self.stageWidget.ChannelComboBox.currentIndex()>0:
                    if len(self.SB_vector_int) == 4 and len(self.BG_vector_int)==2:
                            
                        self.feedbackStatus = True
                        
                    else:
                        self.feedbackStatus = False
                        #self.launch_feedback_btn.setChecked(False)
                        print(1)
                        self.errorbands()
                else:
                    self.feedbackStatus = False
                    #self.launch_feedback_btn.setChecked(False)
                    self.errorstage()
                    
            else:
                self.feedbackStatus = False
                #self.launch_feedback_btn.setChecked(False)
                print(2)
                self.errorscope()
        else:
            self.feedbackStatus = False
            #self.launch_feedback_btn.setChecked(False)
            
            #print(3)
            
            
            
        
          
            #self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
            
            
            
            
    def make_one_little_step(self):
        
        self.stageWidget.GotoPositionAbsolute(self.stageWidget.PositionNmSpinBox.value()+self.stageWidget.StepSpinBox.value())
        
     
    def FeedbackStep(self, data, wanted_delay_position):
        #data: signal from the scope
        #data[0]: list of ToF steps
        #data[1]: list of tensions value (V)
        #wanted delay position in nm
        
        self.Kp = float(self.Kp_display.text())
        
        self.Ti = float(self.Ti_display.text())
        
        self.Td = float(self.Td_display.text())
            
            
        #V1 and V2: current values of integrated sidebands
        V1 = np.trapz(data[1][self.SB_vector_int[0]:self.SB_vector_int[1]])/(self.SB_vector_int[1]-self.SB_vector_int[0]) - np.trapz(data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
        
        
        V2 = np.trapz(data[1][self.SB_vector_int[2]:self.SB_vector_int[3]])/(self.SB_vector_int[3]-self.SB_vector_int[2]) - np.trapz(data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
        
        #print(np.arctan2((V1 - self.O1)/self.A1, (V2 - self.O2)/self.A2))
        
        #calculation of delay with sidebands
        #Dphi = np.unwrap(np.arctan2((V1 - self.O1)/self.A1, (V2 - self.O2)/self.A2))
        Dphi = np.arctan2((V1 - self.O1)/self.A1, (V2 - self.O2)/self.A2)
        
        current_time_delay = Dphi/self.omega  #time delay in s

        #time_delay_error = current_time_delay - wanted_delay
        
        x_position = self.c_m_s*current_time_delay #postion shift in meters
        x_position_nm = x_position*10**9
        
        self.x_error_nm = wanted_delay_position - x_position_nm
        
        
        
        #print(self.x_error_nm)
        
        for i in range(2):
            self.E[i] = self.E[i+1]
        self.E[2] = self.x_error_nm

        self.U[0] = self.U[1]
        
        self.U[1] = self.U[0] + self.Kp*((self.E[2]-self.E[1]) + (self.T/self.Ti)*self.E[2] + (self.Td/self.T)*(self.E[2]-2*self.E[1]+self.E[0]))
        #○self.U[1]=10000.
        self.max_move = int(self.max_move_display.text())
        if self.U[1]<self.max_move:
          
        #move Smaract 
        
            self.stageWidget.GotoPositionAbsolute(int(self.stageWidget.PositionNmLCD.value()+self.U[1]))
            self.stageWidget.PositionNmSpinBox.setValue(int(self.stageWidget.PositionNmLCD.value()+self.U[1]))
            print("platine bouge")
        else:
            self.errormaxmove()
            self.launch_feedback_btn.setChecked(False)
            self.feedbackStatus = False
            
            
    def FeedbackStepTest(self):
        #self.smarActReader.stop()
        self.stageWidget.GotoPositionAbsolute(int(self.stageWidget.PositionNmSpinBox.value()+10))
        print("platine bouge")
        self.stageWidget.PositionNmSpinBox.setValue(int(self.stageWidget.PositionNmSpinBox.value()+10))
        self.stageWidget.PositionFsSpinBox.setValue(self.stageWidget.PositionNmSpinBox.value()/300)
        print(self.stageWidget.PositionFsSpinBox.value())
        #self.smarActReader.run()
        #print(self.stageWidget.PositionNmSpinBox.value())
        #print(self.smarActReader.struct.data2)
        #self.smarActReader.newPosition.emit(self.smarActReader.struct.data2)
        #self.stageWidget.PositionNmLCD.display(self.stageWidget.POS)
        #print("POS = "+str(self.stageWidget.POS))
   
################################ error messages #####################################################
        
    def errorscope(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("You are not connected to the scope, you cannot launch active stabilization.", d)
      
       d.setFixedWidth(475)
       b1.move(50,50)
       d.setWindowTitle("Error")
       d.setWindowModality(QtCore.Qt.ApplicationModal)
       d.exec_()
                
       
    def errorbands(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("You have to select sidebands and background before launching active stabilization.", d)
      
       d.setFixedWidth(475)
       b1.move(50,50)
       d.setWindowTitle("Error")
       d.setWindowModality(QtCore.Qt.ApplicationModal)
       d.exec_()
       
      
    def errorstage(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("You are not connected to the translation stage, you cannot launch active stabilization.", d)
      
       d.setFixedWidth(475)
       b1.move(50,50)
       d.setWindowTitle("Error")
       d.setWindowModality(QtCore.Qt.ApplicationModal)
       d.exec_()
        
       
    def errormaxmove(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("The feedback step exceeded the maximum authorized value.", d)
       d.setFixedWidth(475)
       b1.move(50,50)
       d.setWindowTitle("Error")
       d.setWindowModality(QtCore.Qt.ApplicationModal)
       d.exec_()
           
        
            
            
            
            
            
            
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
  