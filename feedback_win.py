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
        tab
        """
        super(FeedbackTab, self).__init__(parent=None)
        
        
        
        self.live_time_data = [0]
        self.live_error_data = [0]
        self.live_position_data = [0]
        
        self.Kp = 0.1 #servo parameters
        self.Ti = 1.
        self.Td = 0.
        
        self.T = 1  #scope refreshing period in s (used in the PID feedback)
        
        self.U = [0,0]  #two last feedback commands in nm (PID feedback)
        self.E = [0,0,0]  #two last errors in nm (PID feedback)
        
        self.locking_position = 1000
        
        self.max_move = 50  #(nm)
        
        self.feedback_time = 0.   #increments +1 at each feedback step
        
        self.list_error2 = []
        
        self.P = 0
        
        #self.listOfFlippedPoints = []
        
        self.Range = [0,0]
        
        self.storedatafolder = r'C:\Users\mluttmann\Documents\Python Scripts\data\feedbackdata'
        
        self.x_error_nm = 0.
        
        self.feedbackStatus = False   #feedback not running yet
       

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
        self.Ti_display = QtWidgets.QLineEdit("{:.2f}".format(self.Ti), self)
        self.Ti_display.setMaximumWidth(80)
        self.Td_display = QtWidgets.QLineEdit("{:.2f}".format(self.Td), self)
        self.Td_display.setMaximumWidth(80)
        
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
        GainLayout.addWidget(QtWidgets.QLabel("Ti"),1,0)
        GainLayout.addWidget(self.Ti_display,1,1)
        GainLayout.addWidget(QtWidgets.QLabel("Td"),2,0)
        GainLayout.addWidget(self.Td_display,2,1)
        
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
        
        
        
        interactLayout = QtWidgets.QVBoxLayout()
        interactLayout.addWidget(self.ploterror_btn)
        interactLayout.addWidget(self.shapedErrorPlotCanvas)
        interactLayout.addWidget(nav)
        interactLayout.addWidget(ServoGroupBox)
        interactLayout.addWidget(lockingWidget)
        interactLayout.addWidget(maxWidget)
        interactLayout.addWidget(self.storedatafolder_display)
        interactLayout.addWidget(self.launch_feedback_btn)
        interactLayout.addStretch(10)
        #interactLayout.setContentsMargins(100,300,100,300)
        interactLayout.setSpacing(10)
        
        
        box3 = QtWidgets.QHBoxLayout()
        box3.addLayout(displayLayout)
        box3.addLayout(interactLayout)
        
        self.setLayout(box3)
        
        
        
        
        
        
        
        
    def checkFeedback(self):  #gives the authorization for starting the stabilization
        
        if self.launch_feedback_btn.isChecked():
            if self.scopeWidget.scopeGroupBox.isChecked():
                if self.stageWidget.ChannelComboBox.currentIndex()>0:
                    if len(self.tab2.SB_vector_int) == 4 and len(self.tab2.BG_vector_int)==2:
                            
                        self.feedbackStatus = True
                        
                    else:
                        self.feedbackStatus = False
                        self.launch_feedback_btn.setChecked(False)
                        self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
                        print(1)
                        self.errorbands()
                else:
                    self.feedbackStatus = False
                    self.launch_feedback_btn.setChecked(False)
                    self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
                    self.errorstage()
                    
            else:
                self.feedbackStatus = False
                self.launch_feedback_btn.setChecked(False)
                self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
                print(2)
                self.errorscope()
        else:
            self.feedbackStatus = False
            self.launch_feedback_btn.setChecked(False)
            self.launch_feedback_btn.setText("LAUNCH RABBIT \n FEEDBACK")
            
            #print(3)
            
            
            
    def make_one_little_step(self):
        
        self.stageWidget.GotoPositionAbsolute(self.stageWidget.PositionNmSpinBox.value()+self.stageWidget.StepSpinBox.value())
        
     
    def FeedbackStep(self, data, locking_position):
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
      
        #calculation of phase shift with sidebands
        Dphi = np.arctan2((V1 - self.O1)/self.A1, (V2 - self.O2)/self.A2)
    
    
        localErrorSignal = self.list_error2[self.Range[0]:self.Range[1]+1]  # we are only interested in this small part of the error signal around self.locking_position
        localPos = self.tab2.data_x_nm[self.Range[0]:self.Range[1]+1]
        
        localIndexDphi = self.FindX(Dphi, localErrorSignal)
        
        currentPos = localPos[localIndexDphi]
        
        self.x_error_nm = currentPos - locking_position
       
        for i in range(2):
            self.E[i] = self.E[i+1]
        self.E[2] = self.x_error_nm

        self.U[0] = self.U[1]
        
        self.U[1] = self.U[0] + self.Kp*((self.E[2]-self.E[1]) + (self.T/self.Ti)*self.E[2] + (self.Td/self.T)*(self.E[2]-2*self.E[1]+self.E[0]))
       
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
            
            
            

            
            
    def FeedbackStepTest(self):
        
        #self.stageWidget.GotoPositionAbsolute(int(self.stageWidget.PositionNmSpinBox.value()+10))
        print("Translation stage is moving")
        self.stageWidget.PositionNmSpinBox.setValue(int(self.stageWidget.PositionNmSpinBox.value()+10))
        self.stageWidget.PositionFsSpinBox.setValue(self.stageWidget.PositionNmSpinBox.value()/300)
        
        
        
        
        
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
        '''
        plt.plot(self.tab2.data_x_nm,self.list_error2)
        plt.grid()
        plt.show()
        '''
        
        
    def shapedErrorPlotDraw(self):
        self.shapedErrorPlotAxis.clear()
        self.shapeErrorSignal(self.locking_position_display.text())
        self.findRange()
        self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.P], color = 'red')
        print("Range = "+str(self.Range))
        self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.Range[0]], linestyle='--', color =  'black')
        self.shapedErrorPlotAxis.axvline(x = self.tab2.data_x_nm[self.Range[1]], linestyle='--', color = 'black')
        self.shapedErrorPlotAxis.plot(self.tab2.data_x_nm, self.list_error2)
        self.shapedErrorPlotAxis.grid(True)
        self.shapedErrorPlotAxis.set_ylabel("Error signal", fontsize = 10)
        self.shapedErrorPlotAxis.set_xlabel("Delay (nm)", fontsize = 10)
        self.shapedErrorPlotCanvas.draw()
            
    
    
    def findRange(self): 
        
        print("P = "+str(self.P))
        
        '''
        #Min = phase_shift
        k = self.FindX(self.P, self.listOfFlippedPoints)
        print("k = "+str(k))
        print("listOfFlippedPoints = "+str(self.listOfFlippedPoints))
        closest_flipped_point_index = self.listOfFlippedPoints[k]
        if closest_flipped_point_index < self.P:
            self.Range = [closest_flipped_point_index, self.listOfFlippedPoints[k+1]]
        else:
            self.Range = [self.listOfFlippedPoints[k-1], closest_flipped_point_index]
        '''
        max_var_error = 2. # >2 rad variation is taken into account as a tooth
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