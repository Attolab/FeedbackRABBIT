# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 11:48:46 2019

@author: mluttmann
"""
import PyQt5.QtCore as QtCore


from PyQt5.QtGui import QIcon, QFont
from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import Rabbit_scan_stab
import numpy as np


    

class FeedbackTab(QtWidgets.QWidget):
    
    stabScanBtnClicked = QtCore.pyqtSignal(bool)
    
    testStabScanBtnClicked = QtCore.pyqtSignal(bool)
    
    stepOfStabScanFinished = QtCore.pyqtSignal()
    
    stepPercentSignal = QtCore.pyqtSignal(int)
    
    
    def __init__(self,  scopeWin, stageWin, Tab2):
        """
        tab 3: Feedback TAb. Allows the user to select PID parameters, locking position, etc.. and to launch the feedback. In oder to test the program, another widget can be used to generate artificial signals with any level of noise and any drift of the delay.
        """
        super(FeedbackTab, self).__init__(parent=None)
        
        
        
        
        ############################## general variables ##############################
        
        self.live_time_data = [0]
        self.live_error_data = [0]  #contains the list of errors displayed in tab 3
        self.live_position_data = [0]  #contains the list of stage positions displayed in tab 3
        
        self.SBParam = []
        self.PIDParam = []
        
        self.Kp = 1. #servo parameters
        self.Ki = 0.
        self.Kd = 0.
        
        self.T = 1.  #scope refreshing period in s (used in the PID feedback)
        
        self.tMax = 1000
        
        self.feedbackNbr = 1
        
        self.U = [0,0]  #two last feedback commands in nm (PID feedback)
        self.E = [0,0,0]  #two last errors in nm (PID feedback)
        
        self.locking_position = 1000
        
        self.max_error = 25  #(nm)
        
        self.feedback_time = 0.   #increments +1 at each feedback step
        
        self.list_error2 = []
        
        self.P = 0
        
        self.Range = [0,0]
        self.lin_error_signal = []
        self.storedatafolder = r'C:\Users\mluttmann\Documents\Python Scripts\data\feedbackdata'  #where to store data during feedback
        
        self.x_error_nm = 0.   # error value without offset
        self.errorValue = 0.   # error value with offset, will change at each feedback step
        self.currentPos = 0.   # the delay measured with the arctan
        
        self.feedbackStatus = False   #feedback not running yet
        
        self.sum_error = 0.  #statistics for the feedback
        self.square_sum = 0.  #statistics for the feedback
        
        
        ############ test #############
        
        self.drift_speed = 0.2  #nm/s
        #self.locking_position_test = 5000.  #nm
        
        self.drift_frequency = 0.1 #Hz
        self.drift_amp = 20 #nm
        
        self.drift_pos = 0.  # current drift position(initially 0)
        
        self.signal_noise = 0. # between 0 and 1
        
        
        self.list_pos = []    #record of the stage position since the beginning of the feedback (useful for the FFT)
        
        self.list_measured_pos = []    #record of the measured delay since the beginning of the feedback (useful for the FFT)
        
        self.offset_error_signal = 0.
        
        

        ############################### interface ###############################################
       

        self.scopeWidget = scopeWin
        self.stageWidget = stageWin
        
        self.tab2 = Tab2
        
        self.scope2PlotFigure = plt.Figure()
        self.scope2PlotAxis = self.scope2PlotFigure.add_subplot(111, facecolor='k')
        self.scope2PlotCanvas = FigureCanvas(self.scope2PlotFigure)          
        self.scope2PlotCanvas.setMinimumWidth(900)
        self.scope2PlotCanvas.setMinimumHeight(500)
        self.scope2PlotCanvas.setMaximumWidth(900)
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
        
        
        
        
        self.ploterror_btn = QtWidgets.QPushButton("Plot final error signal", self)
        self.ploterror_btn.clicked.connect(self.shapedErrorPlotDraw)
        self.ploterror_btn.setMaximumWidth(130)
        
        self.shapedErrorPlotFigure = plt.Figure()
        self.shapedErrorPlotAxis = self.shapedErrorPlotFigure.add_subplot(111)
        self.shapedErrorPlotCanvas = FigureCanvas(self.shapedErrorPlotFigure)
        self.shapedErrorPlotCanvas.setMinimumWidth(450)
        
        self.shapedErrorPlotAxis.clear()          
        
        
        
        
        self.Kp_display = QtWidgets.QLineEdit("{:.2f}".format(self.Kp), self)
        self.Kp_display.setMaximumWidth(80)
        self.Kp_display.textChanged.connect(self.setKp)
        self.Ki_display = QtWidgets.QLineEdit("{:.2f}".format(self.Ki), self)
        self.Ki_display.setMaximumWidth(80)
        self.Kd_display = QtWidgets.QLineEdit("{:.2f}".format(self.Kd), self)
        self.Kd_display.setMaximumWidth(80)
        
        self.locking_position_display = QtWidgets.QLineEdit("{:.2f}".format(self.locking_position), self)
        self.locking_position_display.setMaximumWidth(80)
        
        self.locking_position_display.textChanged.connect(self.shapeErrorSignal)
        
        self.max_error_display = QtWidgets.QLineEdit("{:.2f}".format(self.max_error), self)
        self.max_error_display.setMaximumWidth(80)
        self.max_error_display.textChanged.connect(self.setMaxError)
        
        self.storedatafolder_display = QtWidgets.QLineEdit("{:.2s}".format(self.storedatafolder), self)
        self.storedatafolder_display.setText(self.storedatafolder)
        self.storedatafolder_display.setMaximumWidth(200)
        
        self.launch_feedback_btn = QtWidgets.QPushButton("LAUNCH RABBIT \n FEEDBACK", self)
        self.launch_feedback_btn.setMaximumWidth(200)
        self.launch_feedback_btn.setCheckable(True)
        self.launch_feedback_btn.setIcon(QIcon('icon_rasta.png'))
        self.launch_feedback_btn.setIconSize(QtCore.QSize(75,75))
        self.launch_feedback_btn.setFont(QFont('SansSerif', 10))
        
                ##### connect buttons
        
        self.launch_feedback_btn.clicked.connect(lambda x : self.StartStopFeedback(x, "Feedback"))
        #self.launch_feedback_btn.setEnabled(True)
        
        self.stab_scan_btn = QtWidgets.QPushButton("Configure stabilized scan", self)
        self.stab_scan_btn.setMaximumWidth(200)
        self.stab_scan_btn.setCheckable(True)

        self.stab_scan_btn.setFont(QFont('SansSerif', 12))        
        self.stab_scan_btn.clicked.connect(self.onClick_stab_scan)
        
        ServoGroupBox = QtWidgets.QGroupBox(self)
        ServoGroupBox.setTitle("Servo parameters")
        
        
        GainLayout = QtWidgets.QGridLayout()
        GainLayout.addWidget(QtWidgets.QLabel("Kp"),0,0)
        GainLayout.addWidget(self.Kp_display,0,1)
        GainLayout.addWidget(QtWidgets.QLabel("Ki"),1,0)
        GainLayout.addWidget(self.Ki_display,1,1)
        GainLayout.addWidget(QtWidgets.QLabel("Kd"),2,0)
        GainLayout.addWidget(self.Kd_display,2,1)
        
        ServoGroupBox.setLayout(GainLayout)
        ServoGroupBox.setFixedWidth(125)
    
        lockingLayout = QtWidgets.QHBoxLayout()
        lockingLayout.addWidget(QtWidgets.QLabel("Locking position (nm)"))
        lockingLayout.addWidget(self.locking_position_display)
        
        
        
        maxLayout = QtWidgets.QHBoxLayout()
        maxLayout.addWidget(QtWidgets.QLabel("Max error (nm)"))
        maxLayout.addWidget(self.max_error_display)
        
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
        
        
        
        nav = NavigationToolbar2QT(self.shapedErrorPlotCanvas, self)
        nav.setStyleSheet("QToolBar { border: 0px }")
        
        
        ################################################################## test
        
        testGroupBox = QtWidgets.QGroupBox()
        testGroupBox.setTitle("Feedback Test")
        testLayout = QtWidgets.QGridLayout()
        
        
        
        self.linearDriftGroupBox = QtWidgets.QGroupBox()
        self.linearDriftGroupBox.setTitle("Linear drift")
        self.linearDriftGroupBox.setCheckable(True)
        #linearDriftGroupBox.setChecked(False)
        linearDriftLayout = QtWidgets.QGridLayout()
        
        
        self.drift_speed_display = QtWidgets.QLineEdit("{:.2f}".format(self.drift_speed), self)
        self.drift_speed_display.setMaximumWidth(80)
        
        linearDriftLayout.addWidget(QtWidgets.QLabel("Drift speed (nm/s)"), 0, 0)
        linearDriftLayout.addWidget(self.drift_speed_display, 0, 1)
        
        self.linearDriftGroupBox.setLayout(linearDriftLayout)
        
        
        self.oscillDriftGroupBox = QtWidgets.QGroupBox()
        self.oscillDriftGroupBox.setTitle("Oscillating drift")
        self.oscillDriftGroupBox.setCheckable(True)
        self.oscillDriftGroupBox.setChecked(False)
        oscillDriftLayout = QtWidgets.QGridLayout()
        
        self.drift_frequency_display = QtWidgets.QLineEdit("{:.2f}".format(self.drift_frequency), self)
        self.drift_frequency_display.setMaximumWidth(80)
        
        self.drift_amp_display = QtWidgets.QLineEdit("{:.2f}".format(self.drift_amp), self)
        self.drift_amp_display.setMaximumWidth(80)
        
        oscillDriftLayout.addWidget(QtWidgets.QLabel("Frequency (Hz)"), 0, 0)
        oscillDriftLayout.addWidget(self.drift_frequency_display, 0, 1)
        oscillDriftLayout.addWidget(QtWidgets.QLabel("Amplitude (nm)"), 1, 0)
        oscillDriftLayout.addWidget(self.drift_amp_display, 1, 1)
        
        self.oscillDriftGroupBox.setLayout(oscillDriftLayout)      
        
        #exclusive tickable box: one drift mode at a time
        
        self.linearDriftGroupBox.toggled.connect(lambda: self.exclusive(self.linearDriftGroupBox, self.oscillDriftGroupBox))
        self.oscillDriftGroupBox.toggled.connect(lambda: self.exclusive(self.oscillDriftGroupBox, self.linearDriftGroupBox))
        
        
        self.signal_noise_display = QtWidgets.QLineEdit("{:.2f}".format(self.signal_noise), self)
        self.signal_noise_display.setMaximumWidth(80)

        
        self.drift_pos_display = QtWidgets.QLCDNumber()
        self.drift_pos_display.setMaximumHeight(30)
        
        #self.locking_position_test_display = QtWidgets.QLineEdit("{:.2f}".format(self.locking_position_test), self)
        #self.locking_position_test_display.setMaximumWidth(80)
        
        self.plot_artificial_signal_btn = QtWidgets.QPushButton("See test signals", self)
        self.plot_artificial_signal_btn.setMaximumWidth(200)
        self.plot_artificial_signal_btn.setCheckable(True)
        self.plot_artificial_signal_btn.clicked.connect(self.testSignalsPlot)
        
        self.plot_fft_btn = QtWidgets.QPushButton("See stage position FFT", self)
        self.plot_fft_btn.setMaximumWidth(200)
        self.plot_fft_btn.setCheckable(True)
        self.plot_fft_btn.clicked.connect(self.FFTPosPlot)
        
        
        self.launch_feedback_test_btn = QtWidgets.QPushButton("LAUNCH RABBIT \n FEEDBACK TEST", self)
        self.launch_feedback_test_btn.setMaximumWidth(200)
        self.launch_feedback_test_btn.setCheckable(True)
        #self.launch_feedback_test_btn.setIcon(QIcon('lapin.png'))
        #self.launch_feedback_test_btn.setIconSize(QtCore.QSize(75,75))
        self.launch_feedback_test_btn.setFont(QFont('SansSerif', 10))
        
        self.test_stab_scan_btn = QtWidgets.QPushButton("Configure stabilized \n test scan", self)
        self.test_stab_scan_btn.setMaximumWidth(200)
        self.test_stab_scan_btn.setCheckable(True)    
        self.stab_scan_btn.setFont(QFont('SansSerif', 9))  
        self.test_stab_scan_btn.clicked.connect(self.onClick_test_stab_scan)        
        #color = QColor(0, 0, 255, 127)
        #color.setNamedColor("transparent blue")
        
        
        self.stab_scan_btn.setStyleSheet("background-color: darkCyan")
        
        #self.launch_feedback_test_btn.clicked.connect(lambda x : self.StartStopFeedback(x, "Test Feedback"))
        
        #testLayout.addWidget(QtWidgets.QLabel("Drift speed (nm/s)"), 0, 0)
        #testLayout.addWidget(self.drift_speed_display, 0, 1)
        testLayout.addWidget(self.linearDriftGroupBox, 0, 0)
        testLayout.addWidget(self.oscillDriftGroupBox, 1, 0)
        testLayout.addWidget(QtWidgets.QLabel("Signal noise"), 2, 0)
        testLayout.addWidget(self.signal_noise_display, 2, 1)
        testLayout.addWidget(self.plot_artificial_signal_btn, 3, 0)
        testLayout.addWidget(QtWidgets.QLabel("Current drift (nm)"), 4, 0)
        testLayout.addWidget(self.drift_pos_display, 4, 1)
        #testLayout.addWidget(QtWidgets.QLabel("Locking position"), 2, 0)
        #testLayout.addWidget(self.locking_position_test_display, 2, 1)
        testLayout.addWidget(self.launch_feedback_test_btn, 5, 0)
        testLayout.addWidget(self.test_stab_scan_btn, 5, 1)
        testLayout.addWidget(self.plot_fft_btn, 6, 0)
        
        testGroupBox.setLayout(testLayout)
        
        
        ######################################################################
        
        
        
        leftWidget = QtWidgets.QWidget()
        leftLayout = QtWidgets.QVBoxLayout()
        
       
        leftLayout.addWidget(ServoGroupBox)
        leftLayout.addWidget(lockingWidget)
        leftLayout.addWidget(maxWidget)
        leftLayout.addWidget(self.storedatafolder_display)
        leftLayout.addWidget(self.launch_feedback_btn)
        leftLayout.addWidget(self.stab_scan_btn)
        #:leftLayout.addStretch(10)
        #interactLayout.setContentsMargins(100,300,100,300)
        #leftLayout.setSpacing(10)
        
        
        leftWidget.setLayout(leftLayout)
        
        
        
        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addWidget(leftWidget)
        bottomLayout.addWidget(testGroupBox)
        
        bottomWidget = QtWidgets.QWidget()
        bottomWidget.setLayout(bottomLayout)
        
        interactLayout = QtWidgets.QVBoxLayout()
        interactLayout.addWidget(self.ploterror_btn)
        interactLayout.addWidget(self.shapedErrorPlotCanvas)
        interactLayout.addWidget(nav)
        interactLayout.addWidget(bottomWidget)
        

        
        interactLayout.addStretch(10)
        #interactLayout.setContentsMargins(100,300,100,300)
        interactLayout.setSpacing(10)
        
        
        box3 = QtWidgets.QHBoxLayout()
        box3.addLayout(displayLayout)
        box3.addLayout(interactLayout)
        
        self.setLayout(box3)
        
        
        
        
############################################################## functions ############################################################
        
        

    def SB_0noise(self, tau, O, A, phi): #SB without noisy, tau in seconds
        return O + A*np.cos(4*self.tab2.omega*tau + phi)
    
    
    def setKp(self, x):
        self.Kp = float(x)
        
    def setMaxError(self, x):
        self.max_error = float(x)
        
    
    def exclusive(self, clickedbox, box2):
        if clickedbox.isChecked():
            box2.setChecked(False)
                
    
        
    def checkFeedback(self):  #gives the authorization for starting the stabilization
        
        if self.launch_feedback_btn.isChecked() or self.launch_feedback_test_btn.isChecked():
            if self.scopeWidget.scopeGroupBox.isChecked():
                if self.stageWidget.ChannelComboBox.currentIndex()>0:
                    if len(self.tab2.SB_vector_int) == 4 and len(self.tab2.BG_vector_int)==2:
                            
                        self.feedbackStatus = True
                        
                    else:
                        self.feedbackStatus = False
                        self.launch_feedback_btn.setChecked(False)
                        self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
                        self.launch_feedback_test_btn.setChecked(False)
                        self.launch_feedback_test_btn.setText("LAUNCH TEST \n FEEDBACK")
                        print(1)
                        self.errorbands()
                else:
                    self.feedbackStatus = False
                    self.launch_feedback_btn.setChecked(False)
                    self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
                    self.launch_feedback_test_btn.setChecked(False)
                    self.launch_feedback_test_btn.setText("LAUNCH TEST \n FEEDBACK")
                    self.errorstage()
                    
            else:
                self.feedbackStatus = False
                self.launch_feedback_btn.setChecked(False)
                self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
                self.launch_feedback_test_btn.setChecked(False)
                self.launch_feedback_test_btn.setText("LAUNCH TEST \n FEEDBACK")
                print(2)
                self.errorscope()
        else:
            self.feedbackStatus = False
            self.launch_feedback_btn.setChecked(False)
            self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
            self.launch_feedback_test_btn.setChecked(False)
            self.launch_feedback_test_btn.setText("LAUNCH TEST \n FEEDBACK")
            
            #print(3)
            
            


    def SB_noisy(self, tau, O, A, phi, noise): #tau in seconds
        return np.random.normal(1, noise)*(O + A*np.cos(4*self.tab2.omega*tau + phi))
      
    
    def lindrift(self, t, t0, drift_speed ):  #in nm
        return t0 + drift_speed*t 
        
    def oscilldrift(self, t, t0, freq, amp):  # in nm
        return t0 + amp*np.sin(2*np.pi*freq*t) 
       
        
#### Construction of local error signal     
        
    def FindX(self, value, List):
        index = 0
        
        Min = abs(List[0] - List[-1])
        for i in range(len(List)):
            diff = abs(List[i] - value)
            if diff<Min:
                Min =  diff
                index = i
        print("Closest array position = " +str(List[index]))
        return index

   
    
    def shapeErrorSignal(self, locking_position):
        #self.listOfFlippedPoints = []
        print(locking_position)
        self.P = self.FindX(float(locking_position), self.tab2.data_x_nm)
        offset = self.tab2.list_error_wrapped[self.P]
        self.list_error2 = []
        for elt in self.tab2.list_error_wrapped:
            self.list_error2.append(elt-offset)
        for i in range(len(self.list_error2)):
            if self.list_error2[i] < -np.pi:
                #self.listOfFlippedPoints.append(i)
                self.list_error2[i]+=2*np.pi
            if self.list_error2[i] > np.pi:
                #self.listOfFlippedPoints.append(i)
                self.list_error2[i]-=2*np.pi
        self.lin_error_signal = []        
        for elt in self.tab2.data_x:
            self.lin_error_signal.append(self.tab2.param_lin[0]*(elt - float(locking_position)/self.tab2.scan_step))

    
    def shapedErrorPlotDraw(self):
        lock = float(self.locking_position_display.text())
        self.shapedErrorPlotAxis.clear()
        self.shapeErrorSignal(self.locking_position_display.text())
        #self.findRange()
        self.shapedErrorPlotAxis.axvline(x = lock, color = 'red')
        #print("Range = "+str(self.Range))
        #self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.Range[0]], linestyle='--', color =  'black')
        #self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.Range[1]], linestyle='--', color = 'black')
        self.shapedErrorPlotAxis.plot(self.tab2.data_x_nm, self.list_error2)
        self.shapedErrorPlotAxis.plot(self.tab2.data_x_nm, self.lin_error_signal)
        print("a = "+str(self.tab2.param_lin[0]))
        self.shapedErrorPlotAxis.set_ylim([-np.pi,np.pi])
        self.shapedErrorPlotAxis.set_xlim([lock-200, lock+200])
        self.shapedErrorPlotAxis.grid(True)
        self.shapedErrorPlotAxis.set_ylabel("Error signal", fontsize = 10)
        self.shapedErrorPlotAxis.set_xlabel("Delay (nm)", fontsize = 10)
        self.shapedErrorPlotCanvas.draw()

        
        
        
################################## updates functions ################################################
        
    def updateFeedbackScreens(self, data, scale_x, scale_y, x_offset, y_offset):
        
       
       
        ########### updates scope screen in tab 3 ################
        self.scope2PlotTrace.set_xdata(data[0])
        self.scope2PlotTrace.set_ydata(data[1])
        self.scope2PlotAxis.set_xlim([x_offset, x_offset + 10*scale_x])
        self.scope2PlotAxis.set_ylim([-4*scale_y + y_offset, 4*scale_y + y_offset])
        self.scope2PlotAxis.grid(True)
        self.scope2PlotAxis.set_ylabel("Tension (V)", fontsize=17)
        self.scope2PlotAxis.set_xlabel("Time (s)", fontsize=17)
       
        if len(self.tab2.SB_vector_int)==4:
            for i in range(4):
                #print(self.tab2.SB_vector[i])
                self.scope2PlotAxis.axvline(x=data[0][self.tab2.SB_vector_int[i]],color='red')
             
        if len(self.tab2.BG_vector_int)==2:   
            for i in range(2):
                self.scope2PlotAxis.axvline(x=data[0][self.tab2.BG_vector_int[i]],color='white')
       
        self.scope2PlotCanvas.draw()
       
        
        ########### updates position and error screens in tab 3 ################
       
        self.time_errorPlotAxis.set_ylim([-100,100])
        self.time_positionPlotAxis.set_ylim([-100,100])
       
        
       
        le = len(self.live_time_data)  #size of the window adapted to the period
        if le*self.T < 30:
            self.live_time_data.append(self.live_time_data[-1]+self.T)
            self.live_error_data.append(self.errorValue)
            self.live_position_data.append(self.stageWidget.PositionNmLCD.value())
            #
            #self.tab3.live_position_data.append(self.tab3.currentPos)
           
        else:
            for i in range(le):
                self.live_time_data[i] += self.T
            for i in range(le-1):
                self.live_error_data[i] = self.live_error_data[i+1]
                self.live_position_data[i] = self.live_position_data[i+1]
                
            
            #print("error value printed = "+str(self.tab3.error_value)) 
            self.live_error_data[-1] = self.errorValue
            self.live_position_data[-1] = self.stageWidget.PositionNmLCD.value()
            #self.tab3.live_position_data[-1] = self.tab3.currentPos
           
           
           
        self.time_errorPlotTrace.set_xdata(self.live_time_data)
        self.time_errorPlotTrace.set_ydata(self.live_error_data)
       
        self.time_errorPlotAxis.set_xlim([self.live_time_data[0], self.live_time_data[-1]])
        #self.tab3.time_errorPlotAxis.set_ylim([1.1*min(-max(self.tab3.live_error_data), min(self.tab3.live_error_data)), 1.1*max(max(self.tab3.live_error_data), -min(self.tab3.live_error_data))])
        Min = min(self.live_error_data)
        Max = max(self.live_error_data)
        y_min = 0
        y_max = 0
        if Min>0:
            y_min = 0.99*Min
        else:
           y_min = 1.01*Min
        if Max>0:
            y_max = 1.01*Max
        else:
            y_max = 0.99*Max
        
        self.time_errorPlotAxis.set_ylim([y_min, y_max])
        
        
        
        self.time_errorPlotAxis.grid(True)
        self.time_errorPlotAxis.set_ylabel("Error (nm)", fontsize=7)
        self.time_errorPlotAxis.set_xlabel("Time (step)", fontsize=7)
       
        self.time_errorPlotCanvas.draw()
       
           
       
        self.time_positionPlotTrace.set_xdata(self.live_time_data)
        self.time_positionPlotTrace.set_ydata(self.live_position_data)
        self.time_positionPlotAxis.set_xlim([self.live_time_data[0], self.live_time_data[-1]])
        #self.tab3.time_positionPlotAxis.set_ylim([1.1*min(-max(self.tab3.live_position_data), min(self.tab3.live_position_data)), 1.1*max(max(self.tab3.live_position_data), -min(self.tab3.live_position_data))])
        Min2 = min(self.live_position_data)
        Max2 = max(self.live_position_data)
        y_min2 = 0
        y_max2 = 0
        if Min2>0:
            y_min2 = 0.99*Min2
        else:
           y_min2 = 1.01*Min2
        if Max2>0:
            y_max2 = 1.01*Max2
        else:
            y_max2 = 0.99*Max2
        
        self.time_positionPlotAxis.set_ylim([y_min2, y_max2])
        
        
        
        
        
        self.time_positionPlotAxis.grid(True)
        self.time_positionPlotAxis.set_ylabel("Delay line position (nm)", fontsize=7)
        self.time_positionPlotAxis.set_xlabel("Time (step)", fontsize=7)
       
        self.time_positionPlotCanvas.draw()
        
      
        
        
################################# popup windows #####################################################
            
    def testSignalsPlot(self):
       self.signal_noise = float(self.signal_noise_display.text())
       TAU = np.linspace(self.tab2.data_x_nm[0], self.tab2.data_x_nm[-1], 400)
       Y1 = []
       Y2 = []
       
       
       for elt in TAU:
           elt = elt*10**(-9)/(self.tab2.c_m_s)  #converts X in time array
           Y1.append(self.SB_noisy(elt, self.tab2.O1, self.tab2.A1, self.tab2.phi1, self.signal_noise))
           Y2.append(self.SB_noisy(elt, self.tab2.O2, self.tab2.A2, self.tab2.phi2, self.signal_noise))
           
           #with perfect phase quadrature
           #Y2.append(self.SB(elt, self.tab2.O2, self.tab2.A2, self.tab2.phi1-np.pi/2, self.signal_noise))
    

       fig = plt.figure("Shape of test signals")  
       ax = fig.add_subplot(1, 1, 1)
       ax.plot(TAU, Y1, label="Test signal SB1", color="green")
       ax.plot(TAU, Y2, label="Test signal SB2", color="red")
       
       ax.set_ylabel("Signal (V)", fontsize=10)
       ax.set_xlabel("Delay (nm)", fontsize=10)
       ax.legend(loc='best')
       
       plt.show()
       
       

       
       
            
       self.plot_artificial_signal_btn.setChecked(False)
       
       
       
    def FFTPosPlot(self):
      
       
       fftpos = np.fft.fft(self.list_pos[1:])
       fftmespos = np.fft.fft(self.list_measured_pos[1:])
       #for elt in fftpos:
       #   elt = abs(elt)
       n = len(self.list_pos[1:])
       freqs = np.fft.fftfreq(n, 1.)
       np.fft.fftshift(freqs)

       halffft = fftpos[:int(n/2)]
       halffft2 = fftmespos[:int(n/2)]
       halffreqs = freqs[:int(n/2)]
       fig = plt.figure("Delay FFT, t = " +str(self.feedback_time) + ", noise = " +str(self.signal_noise) + ", Kp = "+str(self.Kp)+", Ki = "+str(self.Ki))  
       ax = fig.add_subplot(1, 1, 1)
       
       ax.plot(halffreqs, abs(halffft), color="black", label = "No stabilization")
       ax.plot(halffreqs, abs(halffft2), color="red", label = "Stabilization")
       #print(fftpos)
       ax.set_ylabel("Amplitude (a.u)", fontsize=30)
       ax.set_xlabel("Frequency (Hz)", fontsize=30)
       ax.set_ylim([0,4000])
       ax.legend(loc='best')
       
       plt.show()
            
       self.plot_fft_btn.setChecked(False)
       
       
       
       
       
       
    def onClick_stab_scan(self):
        self.stab_scan_btn.setChecked(False)
        
        if not self.scopeWidget.scopeGroupBox.isChecked():
            self.errorscope()
            return
        
        if not self.stageWidget.ChannelComboBox.currentIndex()>0:
            self.errorstage()
            return
        
        if len(self.tab2.param_lin) == 0:
            self.errorerrorsignal()
            return
    
        stab_scan_widget = Rabbit_scan_stab.ScanStabWidget(self, "scan stab")
        stab_scan_widget.mvtTypeComboBox.addItem("Forward") #impossible to put this command in the scan ui file, I don't know why
        stab_scan_widget.mvtTypeComboBox.addItem("Backward")
        
        dialog = QtWidgets.QDialog()
        
        box = QtWidgets.QHBoxLayout()
        
       
        winLayout=QtWidgets.QVBoxLayout()
        winLayout.addWidget(stab_scan_widget)
        
        box.addLayout(winLayout)
        #box.addWidget(self.scopePlotCanvas)
       
      
        dialog.setLayout(box)
        dialog.setWindowModality(1)
        dialog.exec_()
        
        
        
    def onClick_test_stab_scan(self):
        #self.stab_scan_btn.setChecked(False)
        self.test_stab_scan_btn.setChecked(False)
        
        if not self.scopeWidget.scopeGroupBox.isChecked():
            self.errorscope()
            return
        
        if not self.stageWidget.ChannelComboBox.currentIndex()>0:
            self.errorstage()
            return
        
        if len(self.tab2.param_lin) == 0:
            self.errorerrorsignal()
            return
    
        test_stab_scan_widget = Rabbit_scan_stab.ScanStabWidget(self, "test scan stab")
        test_stab_scan_widget.titleLabel.setText("Test Stab Scan")
        test_stab_scan_widget.mvtTypeComboBox.addItem("Forward") #impossible to put this command in the scan ui file, I don't know why
        test_stab_scan_widget.mvtTypeComboBox.addItem("Backward")
        
        dialog = QtWidgets.QDialog()
        
        box = QtWidgets.QHBoxLayout()
       
       
        winLayout=QtWidgets.QVBoxLayout()
        winLayout.addWidget(test_stab_scan_widget)
        
        box.addLayout(winLayout)
        #box.addWidget(self.scopePlotCanvas)
       
      
        dialog.setLayout(box)
        dialog.setWindowModality(1)
        dialog.exec_()
   
################################ error messages #####################################################
        
    def errorscope(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("Scope not connected", d)
      
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
       
       
       
    def errorerrorsignal(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("You have to generate an error signal before launching active stabilization", d)
      
       d.setFixedWidth(475)
       b1.move(50,50)
       d.setWindowTitle("Error")
       d.setWindowModality(QtCore.Qt.ApplicationModal)
       d.exec_()
       
      
    def errorstage(self):
       d = QtWidgets.QDialog()
       
       b1 = QtWidgets.QLabel("SmarAct not connected", d)
      
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
       
   