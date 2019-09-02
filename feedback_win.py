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

import numpy as np

class FeedbackTab(QtWidgets.QWidget):
    def __init__(self,  scopeWin, stageWin, Tab2):
        """
        tab 3: Feedback TAb. Allows the user to select PID parameters, locking position, etc.. and to launch the feedback. In oder to test the program, another widget can be used to generate artificial signals with any level of noise and any drift of the delay.
        """
        super(FeedbackTab, self).__init__(parent=None)
        
        
        
        
        ############################## general variables ##############################
        
        self.live_time_data = [0]
        self.live_error_data = [0]  #contains the list of errors displayed in tab 3
        self.live_position_data = [0]  #contains the list of stage positions displayed in tab 3
        
        self.Kp = 0.1 #servo parameters
        self.Ki = 0.
        self.Kd = 0.
        
        self.T = 1.  #scope refreshing period in s (used in the PID feedback)
        
        self.U = [0,0]  #two last feedback commands in nm (PID feedback)
        self.E = [0,0,0]  #two last errors in nm (PID feedback)
        
        self.locking_position = 5000
        
        self.max_move = 100  #(nm)
        
        self.feedback_time = 0.   #increments +1 at each feedback step
        
        self.list_error2 = []
        
        self.P = 0
        
        self.Range = [0,0]
        self.lin_error_signal = []
        self.storedatafolder = r'C:\Users\mluttmann\Documents\Python Scripts\data\feedbackdata'  #where to store data during feedback
        
        self.x_error_nm = 0.   # error value, will change at each feedback step
        
        self.currentPos = 0.   # the delay measured with the arctan
        
        self.feedbackStatus = False   #feedback not running yet
        
        self.sum_error = 0.  #statistics for the feedback
        self.square_sum = 0.  #statistics for the feedback
        
        
        ############ test #############
        
        self.drift_speed = 0.27  #nm/s
        self.locking_position_test = 5000.  #nm
        
        self.drift_frequency = 0.1 #Hz
        self.drift_amp = 20 #nm
        
        self.drift_pos = 0.  # current drift position(initially 0)
        
        self.signal_noise = 0.1 # between 0 and 1
        
        
        self.list_pos = []    #record of the stage position since the beginning of the feedback (useful for the FFT)
        
        self.list_measured_pos = []    #record of the measured delay since the beginning of the feedback (useful for the FFT)
        
        

        ############################### interface ###############################################
       

        self.scopeWidget = scopeWin
        self.stageWidget = stageWin
        
        self.tab2 = Tab2
        
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
        self.Ki_display = QtWidgets.QLineEdit("{:.2f}".format(self.Ki), self)
        self.Ki_display.setMaximumWidth(80)
        self.Kd_display = QtWidgets.QLineEdit("{:.2f}".format(self.Kd), self)
        self.Kd_display.setMaximumWidth(80)
        
        self.locking_position_display = QtWidgets.QLineEdit("{:.2f}".format(self.locking_position), self)
        self.locking_position_display.setMaximumWidth(80)
        
        self.locking_position_display.textChanged.connect(self.shapeErrorSignal)
        
        self.max_move_display = QtWidgets.QLineEdit("{:.2f}".format(self.max_move), self)
        self.max_move_display.setMaximumWidth(80)
        
        self.storedatafolder_display = QtWidgets.QLineEdit("{:.2s}".format(self.storedatafolder), self)
        self.storedatafolder_display.setText(self.storedatafolder)
        self.storedatafolder_display.setMaximumWidth(200)
        
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
        
        
        self.launch_feedback_test_btn = QtWidgets.QPushButton("LAUNCH TEST \n FEEDBACK", self)
        self.launch_feedback_test_btn.setMaximumWidth(200)
        self.launch_feedback_test_btn.setCheckable(True)
        #self.launch_feedback_test_btn.setIcon(QIcon('lapin.png'))
        #self.launch_feedback_test_btn.setIconSize(QtCore.QSize(75,75))
        self.launch_feedback_test_btn.setFont(QFont('SansSerif', 10))
        
        self.launch_feedback_test_btn.clicked.connect(self.checkFeedback)
        
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
            
            
            
    def make_one_little_step(self): #just a test
        
        self.stageWidget.GotoPositionAbsolute(self.stageWidget.PositionNmSpinBox.value()+self.stageWidget.StepSpinBox.value())
        
'''    
    def FeedbackStep(self, data, locking_position):  # performs one feedback step
        #data: signal from the scope
        #data[0]: list of ToF steps
        #data[1]: list of tensions value (V)
        #wanted delay position in nm
        
        self.Kp = float(self.Kp_display.text())
        
        self.Ki = float(self.Ki_display.text())
        
        self.Kd = float(self.Kd_display.text())
            
            
        #V1 and V2: current values of integrated sidebands
        V1 = np.trapz(data[1][self.SB_vector_int[0]:self.SB_vector_int[1]])/(self.SB_vector_int[1]-self.SB_vector_int[0]) - np.trapz(data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
        
        
        V2 = np.trapz(data[1][self.SB_vector_int[2]:self.SB_vector_int[3]])/(self.SB_vector_int[3]-self.SB_vector_int[2]) - np.trapz(data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
      
        #calculation of phase shift with sidebands
        Dphi = np.arctan2((V1 - self.O1)/self.A1, (V2 - self.O2)/self.A2)
        
        '''
        '''
        
        localErrorSignal = self.list_error2[self.Range[0]:self.Range[1]+1]  # we are only interested in this small part of the error signal around self.locking_position
        localPos = self.tab2.data_x_nm[self.Range[0]:self.Range[1]+1]
        
        localIndexDphi = self.FindX(Dphi, localErrorSignal)
        
        currentPos = localPos[localIndexDphi]
        
       
        
        self.x_error_nm = currentPos - locking_position
       
        for i in range(2):
            self.E[i] = self.E[i+1]
        self.E[2] = self.x_error_nm

        self.U[0] = self.U[1]
        
        self.U[1] = self.U[0] + self.Kp*(self.E[2]-self.E[1]) + self.T*self.Ki*self.E[2] + (self.Kd/self.T)*(self.E[2]-2*self.E[1]+self.E[0])
       
        self.max_move = int(self.max_move_display.text())
        if self.U[1] < self.max_move:
          
        #move Smaract 
        
            #self.stageWidget.GotoPositionAbsolute(int(self.stageWidget.PositionNmLCD.value() - self.U[1]))
            self.stageWidget.PositionNmSpinBox.setValue(int(self.stageWidget.PositionNmLCD.value() - self.U[1]))
            
            print("Translation stage is moving")
        else:
            self.errormaxmove()
            self.launch_feedback_btn.setChecked(False)
            self.feedbackStatus = False
'''            
            
            
    def FeedbackStep(self, data, time):  # performs one feedback step. Time in seconds
        

        locking_position = float(self.locking_position_display.text())
        
        
        print("time = "+str(time))
 
        V1 = np.trapz(data[1][self.SB_vector_int[0]:self.SB_vector_int[1]])/(self.SB_vector_int[1]-self.SB_vector_int[0]) - np.trapz(data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
        V2 = np.trapz(data[1][self.SB_vector_int[2]:self.SB_vector_int[3]])/(self.SB_vector_int[3]-self.SB_vector_int[2]) - np.trapz(data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
        
        print("V1 = "+str(V1))
        print("V2 = "+str(V2))
 

        # measurement of the phase shift in the interferometer
        Dphi = np.arctan2((V1 - self.tab2.O1)/self.tab2.A1, (V2 - self.tab2.O2)/self.tab2.A2)  
        
        print("Dphi = "+str(Dphi))
    
        a = self.tab2.param_lin[0]/self.tab2.scan_step  #slope of the error signal
        
        # the error signal is y(x) = Dphi = a*(x - locking_position), therefore:

        self.currentPos = Dphi/a + locking_position   # current measured delay
        print("currentPos ="+str(self.currentPos))

        self.x_error_nm = self.currentPos - locking_position  # current error value
            
        if time > 1:
            self.sum_error += abs(new_distance)
            print("distance from theory = "+str(new_distance))
            average_distance = self.sum_error/(time-1)
            print("average distance from theory ="+str(average_distance))
            self.square_sum+=(new_distance - average_distance)**2
            standard_deviation = np.sqrt(self.square_sum/(time-1))
            print("standard deviation ="+str(standard_deviation))
        
        
        if len(self.list_pos) == 0:
            self.list_pos.append(self.stageWidget.PositionNmLCD.value())
        else:
            
            self.list_pos.append(self.list_pos[-1]+self.x_error_nm)
        #self.list_pos.append(self.x_error_nm)
        self.list_measured_pos.append(self.currentPos)

        
        
        
        ############################ PID ################################
        
        
        self.Kp = float(self.Kp_display.text())
        self.Ki = float(self.Ki_display.text())
        self.Kd = float(self.Kd_display.text())
        
        
        
        
        for i in range(2):
            self.E[i] = self.E[i+1]
        self.E[2] = self.x_error_nm

        self.U[0] = self.U[1]
        
        self.U[1] = self.U[0] + self.Kp*(self.E[2]-self.E[1]) + self.T*self.Ki*self.E[2] + (self.Kd/self.T)*(self.E[2]-2*self.E[1]+self.E[0])
        
        self.max_move = int(float(self.max_move_display.text()))
        
        if self.U[1] < self.max_move:
        #move Smaract 
        
            
            self.stageWidget.PositionNmSpinBox.setValue(int(self.stageWidget.PositionNmLCD.value()+ self.U[1]))
            
            print("Translation stage is moving")
        else:
            self.errormaxmove()
            self.launch_feedback_test_btn.setChecked(False)
            self.feedbackStatus = False

        print("")
        
        
            

########################## FeedbackTest ##########################################
    
    def SB(self, tau, O, A, phi, noise): #tau in seconds
        return np.random.normal(1, noise)*(O + A*np.cos(4*self.tab2.omega*tau + phi))
    
    
    def lindrift(self, t, t0, drift_speed ):  #in nm
        return t0 + drift_speed*t 
        
    def oscilldrift(self, t, t0, freq, amp):  # in nm
        return t0 + amp*np.sin(2*np.pi*freq*t) 
    
    def FeedbackStepTest(self, time):  # performs one feedback step, in "test mode". Time in seconds
        
        
        drift_speed = float(self.drift_speed_display.text())
        drift_freq = float(self.drift_frequency_display.text())
        drift_amp = float(self.drift_amp_display.text())
        locking_position = float(self.locking_position_display.text())
        
        
        print("time = "+str(time))
 
          
        compensation_shift = self.stageWidget.PositionNmLCD.value() - locking_position #how much we've moved so far 
        # WARNING critical : self.stageWidget.PositionNmLCD.value() doesnt have time to update at time = 0, therefore equals 0 . Works for time > 0
        print("positionNmLCD = "+str(self.stageWidget.PositionNmLCD.value()))
        print("compensation shift = "+str(compensation_shift))
        
        
        if self.linearDriftGroupBox.isChecked():
            current_tau_nm = self.lindrift(time, locking_position, drift_speed) 
        
        
        if self.oscillDriftGroupBox.isChecked():
            current_tau_nm = self.oscilldrift(time, locking_position, drift_freq, drift_amp)
        
  
        print("current tau not compensated (nm) = "+str(current_tau_nm))
        current_tau_nm_compensated = current_tau_nm - compensation_shift # this is the relevant delay to be used in the test signals
        current_tau_s_compensated = current_tau_nm_compensated*10**(-9)/self.tab2.c_m_s  # delay in seconds
        print("current compensated delay (nm) = "+str(current_tau_nm_compensated))
        
     
        self.signal_noise = float(self.signal_noise_display.text())
        
        #with compensation due to feedback
        V1 = self.SB(current_tau_s_compensated, self.tab2.O1, self.tab2.A1, self.tab2.phi1, self.signal_noise)
        V2 = self.SB(current_tau_s_compensated, self.tab2.O2, self.tab2.A2, self.tab2.phi2, self.signal_noise)
        
        print("V1 = "+str(V1))
        print("V2 = "+str(V2))
 

        # measurement of the phase shift in hte interferometer
        Dphi = np.arctan2((V1 - self.tab2.O1)/self.tab2.A1, (V2 - self.tab2.O2)/self.tab2.A2)  
        
        print("Dphi = "+str(Dphi))
    
        a = self.tab2.param_lin[0]/self.tab2.scan_step  #slope of the error signal
        
        # the error signal is y(x) = Dphi = a*(x - locking_position), therefore:

        self.currentPos = Dphi/a + locking_position   # current measured delay
        print("currentPos ="+str(self.currentPos))

        self.x_error_nm = self.currentPos - locking_position  # current error value
       
        
        new_distance  = abs(self.stageWidget.PositionNmLCD.value() - current_tau_nm)  # distance between the position of the stage and its ideal position (useful for FFT)
        
        
        if time > 1:
            self.sum_error += abs(new_distance)
            print("distance from theory = "+str(new_distance))
            average_distance = self.sum_error/(time-1)
            print("average distance from theory ="+str(average_distance))
            self.square_sum+=(new_distance - average_distance)**2
            standard_deviation = np.sqrt(self.square_sum/(time-1))
            print("standard deviation ="+str(standard_deviation))
        
        
        if len(self.list_pos) == 0:
            self.list_pos.append(self.stageWidget.PositionNmLCD.value())
        else:
            
            self.list_pos.append(self.list_pos[-1]+self.x_error_nm)
        #self.list_pos.append(self.x_error_nm)
        self.list_measured_pos.append(self.currentPos)
        
        self.drift_pos_display.display(current_tau_nm - locking_position)
        
        
        
        ############################ PID ################################
        
        
        self.Kp = float(self.Kp_display.text())
        self.Ki = float(self.Ki_display.text())
        self.Kd = float(self.Kd_display.text())
        
        
        
        
        for i in range(2):
            self.E[i] = self.E[i+1]
        self.E[2] = self.x_error_nm

        self.U[0] = self.U[1]
        
        self.U[1] = self.U[0] + self.Kp*(self.E[2]-self.E[1]) + self.T*self.Ki*self.E[2] + (self.Kd/self.T)*(self.E[2]-2*self.E[1]+self.E[0])
        
        self.max_move = int(float(self.max_move_display.text()))
        
        if self.U[1] < self.max_move:
        #move Smaract 
        
            
            self.stageWidget.PositionNmSpinBox.setValue(int(self.stageWidget.PositionNmLCD.value()+ self.U[1]))
            
            print("Translation stage is moving")
        else:
            self.errormaxmove()
            self.launch_feedback_test_btn.setChecked(False)
            self.feedbackStatus = False

        print("")




##########################################################################################################     
        
        
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
        self.shapedErrorPlotAxis.clear()
        self.shapeErrorSignal(self.locking_position_display.text())
        self.findRange()
        self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.P], color = 'red')
        print("Range = "+str(self.Range))
        self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.Range[0]], linestyle='--', color =  'black')
        self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.Range[1]], linestyle='--', color = 'black')
        self.shapedErrorPlotAxis.plot(self.tab2.data_x_nm, self.list_error2)
        self.shapedErrorPlotAxis.plot(self.tab2.data_x_nm, self.lin_error_signal)
        print("a = "+str(self.tab2.param_lin[0]))
        self.shapedErrorPlotAxis.set_ylim([-np.pi,np.pi])
        self.shapedErrorPlotAxis.grid(True)
        self.shapedErrorPlotAxis.set_ylabel("Error signal", fontsize = 10)
        self.shapedErrorPlotAxis.set_xlabel("Delay (nm)", fontsize = 10)
        self.shapedErrorPlotCanvas.draw()
            
    
    
    def findRange(self): 
        
        print("P = "+str(self.P))
        

        max_var_error = 2.5 # >2 rad variation is taken into account as a tooth
        loop = True
        i = self.P
        while loop == True: # first loop: looks forward for sudden variations
            if abs(self.list_error2[i] - self.list_error2[i+1]) > max_var_error:
                self.Range[1] = i
                print
                loop = False
            i += 1
        i = self.P
        loop = True
        while loop == True: # second loop: looks backward for sudden variations
            if abs(self.list_error2[i] - self.list_error2[i-1]) > max_var_error:
                self.Range[0] = i
                loop = False
            i -= 1
            
      
        
        
################################# popup windows #####################################################
            
    def testSignalsPlot(self):
       self.signal_noise = float(self.signal_noise_display.text())
       TAU = np.linspace(self.tab2.data_x_nm[0], self.tab2.data_x_nm[-1], 400)
       Y1 = []
       Y2 = []
       
       for elt in TAU:
           elt = elt*10**(-9)/(self.tab2.c_m_s)  #converts X in time array
           Y1.append(self.SB(elt, self.tab2.O1, self.tab2.A1, self.tab2.phi1, self.signal_noise))
           Y2.append(self.SB(elt, self.tab2.O2, self.tab2.A2, self.tab2.phi2, self.signal_noise))
       
    

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