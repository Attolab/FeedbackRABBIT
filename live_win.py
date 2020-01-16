# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 11:14:36 2019

@author: mluttmann
"""


from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
import PyQt5.QtCore as QtCore

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

from Scope_f import ScopeWidget
from SmarAct_f import StageWidget
from Rabbit_scan import ScanWidget

class LiveTab(QtWidgets.QWidget):
    def __init__(self, parent = None):
        """
        tab 1: Live Tab. Allows the user to conenct to the scope, the stage, and to perform a RABBIT scan.
        """
        super(LiveTab, self).__init__(parent=None)

        self.scopeWidget = ScopeWidget()
        self.stageWidget = StageWidget()
        self.scanWidget = ScanWidget()
        
        self.scanWidget.mvtTypeComboBox.addItem("Forward") #impossible to put this command in the scan ui file, I don't know why
        self.scanWidget.mvtTypeComboBox.addItem("Backward")
        
        self.nbr_clicks_SB = 0
        self.nbr_clicks_Harm = 0
        self.nbr_clicks_BG = 0
        
        self.SBVector = []
        self.HarmVector = []
        self.BGVector = []
        
        self.SBVector_points = []
        self.HarmVector_points = []
        self.BGVector_points = []
        
        self.intensityRatio = 0.
        
        self.live_ratio_data = [0]
        self.live_time_data  = [0]      
        ########### INTERFACE ##############
   
        
        self.scopePlotFigure = plt.Figure()
        self.scopePlotAxis = self.scopePlotFigure.add_subplot(111, facecolor='k')
        self.scopePlotCanvas = FigureCanvas(self.scopePlotFigure)          
        self.scopePlotCanvas.setMinimumWidth(250)
        self.scopePlotCanvas.setMinimumHeight(600)
        #self.scopePlotCanvas.setMaximumWidth(1000)
        self.scopePlotCanvas.setMaximumHeight(600)
       
        self.scopePlotTrace, = self.scopePlotAxis.plot([0,1],[0,0],color='yellow')
       
        self.scopePlotCanvas.mpl_connect('button_press_event', self.onclick) 
        
        box = QtWidgets.QHBoxLayout()
       
       
        winLayout=QtWidgets.QVBoxLayout()
        winLayout.addWidget(self.scopeWidget)
        winLayout.addWidget(self.stageWidget)
        winLayout.addWidget(self.scanWidget)
        winLayout.setSpacing(120)
        
       
        imageWidget = QtWidgets.QLabel()
        #imageWidget.setMaximumWidth(1000)
        pix = QPixmap('logo.png')
        scaledpix = pix.scaled(300,500, QtCore.Qt.KeepAspectRatio)

        imageWidget.setPixmap(scaledpix)
        imageWidget.setParent(self)
        imageWidget.move(1180,650)
        
        emptywidget = QtWidgets.QLabel()
        
        ratioGroupBox = QtWidgets.QGroupBox(self)
        ratioGroupBox.setTitle("SB/Harm intensity ratio")
        
        self.SBCheckBox = QtWidgets.QCheckBox("Select sideband peak")
        self.SBCheckBox.setStyleSheet("QCheckBox {color: blue}")
        self.HarmCheckBox = QtWidgets.QCheckBox("Select harmonic peak")
        self.HarmCheckBox.setStyleSheet("QCheckBox {color: green}")
        self.BGCheckBox = QtWidgets.QCheckBox("Select a background band")
        #self.BGCheckBox.setStyleSheet("QCheckBox {color: grey}")
        
        self.SBCheckBox.stateChanged.connect(lambda: self.exclusive(self.SBCheckBox, self.HarmCheckBox, self.BGCheckBox))
        self.HarmCheckBox.stateChanged.connect(lambda: self.exclusive(self.HarmCheckBox, self.SBCheckBox, self.BGCheckBox))
        self.BGCheckBox.stateChanged.connect(lambda: self.exclusive(self.BGCheckBox, self.SBCheckBox, self.HarmCheckBox))        
    
    

        ratioLayout = QtWidgets.QHBoxLayout()
        ratioLayout.addWidget(self.SBCheckBox)
        ratioLayout.addWidget(self.HarmCheckBox)
        ratioLayout.addWidget(self.BGCheckBox)

        ratioGroupBox.setLayout(ratioLayout)
        ratioGroupBox.setMaximumWidth(550)
        
        self.time_ratioPlotFigure = plt.Figure()
        self.time_ratioPlotAxis = self.time_ratioPlotFigure.add_subplot(111, facecolor='k')
        self.time_ratioPlotCanvas = FigureCanvas(self.time_ratioPlotFigure)          
        #self.time_errorPlotCanvas.setMinimumWidth(1000)
        #self.time_errorPlotCanvas.setMinimumHeight(100)
        self.time_ratioPlotCanvas.setMaximumWidth(800)
        self.time_ratioPlotCanvas.setMaximumHeight(200)
       
        self.time_ratioPlotTrace, = self.time_ratioPlotAxis.plot([0,1],[0,0],color='yellow')        
        
        
        
        
        
        
        
        
        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(ratioGroupBox)
        rightLayout.addWidget(self.scopePlotCanvas)
        rightLayout.addWidget(self.time_ratioPlotCanvas)
        rightLayout.addWidget(emptywidget)
        rightLayout.setSpacing(10)


        bottomLabel = QtWidgets.QLabel("RASta (RABBIT Active Stabilisation) - ATTOLab - CEA - 2019")
        bottomLabel.setParent(self) 
        bottomLabel.move(1200,715)
        
        
        box.addLayout(winLayout)
        box.addLayout(rightLayout)
      
        self.setLayout(box)
        

    ############################### functions ####################################
        
    ###################### updating the live screen  ##############################
        
        
    def updateLiveScreen(self, data, scale_x, scale_y, x_offset, y_offset):
        
   
        self.scopePlotTrace.set_xdata(data[0])
        self.scopePlotTrace.set_ydata(data[1])
        self.scopePlotAxis.set_xlim([x_offset, x_offset + 10*scale_x])
        self.scopePlotAxis.set_ylim([-4*scale_y + y_offset, 4*scale_y + y_offset])
        self.scopePlotAxis.grid(True)
        self.scopePlotAxis.set_ylabel("Tension (V)", fontsize=17)
        self.scopePlotAxis.set_xlabel("Time (s)", fontsize=17)
        self.scopePlotCanvas.draw()      
        
        #need to put here the vertical lines for the intensity contrast calculation
        '''
        for x in self.SBVector:
            self.scopePlotAxis.axvline(x,color='blue')
        for x in self.HarmVector:
            self.scopePlotAxis.axvline(x,color='green')
        for x in self.BGVector:
            self.scopePlotAxis.axvline(x,color='white')
        self.scopePlotCanvas.draw() 

        '''

        self.time_ratioPlotAxis.set_ylim([-100,100])
             
        if (len(self.SBVector) == 2) and (len(self.HarmVector) == 2) and (len(self.BGVector) == 2):
             
            self.tof2int(data) 

            #print("self.BGVector_points = " +str(self.BGVector_points))
            #print("len data = " +str(len(data[1])))
            BG_intensity = np.trapz(data[1][self.BGVector_points[0]:self.BGVector_points[1]])/abs(self.BGVector_points[1]-self.BGVector_points[0])
            #print("data[1][self.BGVector_points[0]] = "+str(data[1][self.BGVector_points[0]]))
            #print("BG_intensity = "+str(BG_intensity))  
                    
            retrieved_data = data[1] - BG_intensity
            norm = np.trapz(retrieved_data)
            shaped_data = retrieved_data/norm
            
            #SB_intensity =  np.trapz(data[1][self.SBVector_points[0]:self.SBVector_points[1]])/abs(self.SBVector_points[1]-self.SBVector_points[0]) \
                   # - BG_intensity
            SB_intensity = np.trapz(shaped_data[self.SBVector_points[0]:self.SBVector_points[1]])/abs(self.SBVector_points[1]-self.SBVector_points[0])
            #print("self.SBVector_points = " +str(self.SBVector_points))
            #print("SB_intensity = "+str(SB_intensity))                     
            
            #Harm_intensity = np.trapz(data[1][self.HarmVector_points[0]:self.HarmVector_points[1]])/abs(self.HarmVector_points[1]-self.HarmVector_points[0]) \
                    #- BG_intensity
            Harm_intensity = np.trapz(shaped_data[self.HarmVector_points[0]:self.HarmVector_points[1]])/abs(self.HarmVector_points[1]-self.HarmVector_points[0])
            #print("self.HarmVector_points = " +str(self.HarmVector_points))
            #print("data[1][self.HarmVector_points[0]] = "+str(data[1][self.HarmVector_points[0]]))
            #print("Harm_intensity = "+str(Harm_intensity))             
            
            self.intensityRatio = abs(SB_intensity/Harm_intensity)            
            
            #print("intensity ratio = " +str(self.intensityRatio))
            
        le = len(self.live_time_data)  #size of the window adapted to the period
        if le < 30:
            self.live_time_data.append(self.live_time_data[-1]+1)
            #print("intensity ratio = " +str(self.intensityRatio))
            self.live_ratio_data.append(self.intensityRatio)
        else:
            for i in range(le):
                self.live_time_data[i] += 1
            for i in range(le-1):
                self.live_ratio_data[i] = self.live_ratio_data[i+1]
                
            self.live_ratio_data[-1] = self.intensityRatio
 
        ################################################################################################

      
        self.time_ratioPlotTrace.set_xdata(self.live_time_data)
        self.time_ratioPlotTrace.set_ydata(self.live_ratio_data)
        self.time_ratioPlotAxis.set_xlim([self.live_time_data[0], self.live_time_data[-1]])
        
        Min3 = min(self.live_ratio_data)
        Max3 = max(self.live_ratio_data)
        y_min3 = Min3 - 0.00001
        y_max3 = Max3 + 0.00001
        '''
        if Min3>0:
            y_min3 = 0.99*Min3
        else:
           y_min3 = 1.01*Min3
        if Max3>0:
            y_max3 = 1.01*Max3
        else:
            y_max3 = 0.99*Max3
        '''
        self.time_ratioPlotAxis.set_ylim([y_min3, y_max3])
 
        
        self.time_ratioPlotAxis.grid(True)
        self.time_ratioPlotAxis.set_ylabel("Intensity ratio", fontsize=10)
        self.time_ratioPlotAxis.set_xlabel("Number of acquisitions", fontsize=2)
       
        self.time_ratioPlotCanvas.draw()
        
       
        
    def exclusive(self, clickedbox, box2, box3):
        if clickedbox.isChecked():
            box2.setChecked(False)
            box3.setChecked(False)
            
    def onclick(self, event):

        if self.SBCheckBox.isChecked():
            if self.nbr_clicks_SB == 2:
                self.SBVector = []
                self.nbr_clicks_SB = 0
                print("SBVector ="+str(self.SBVector))
                self.SB1.remove()
                self.SB2.remove()
                print("lines =" +str(self.scopePlotAxis.lines))
                self.scopePlotCanvas.draw() 
                
            else:
                x = event.xdata
                if self.nbr_clicks_SB == 0:
                    self.SB1 = self.scopePlotAxis.axvline(x,color='blue')
                    self.scopePlotCanvas.draw()
                if self.nbr_clicks_SB == 1:
                    self.SB2 = self.scopePlotAxis.axvline(x,color='blue')
                    self.scopePlotCanvas.draw()
                self.SBVector.append(x)
                  
                self.nbr_clicks_SB += 1
                self.SBVector.sort()    
                print("SBVector ="+str(self.SBVector))
                print("lines =" +str(self.scopePlotAxis.lines))


      
        if self.HarmCheckBox.isChecked():
            if self.nbr_clicks_Harm == 2:
                self.HarmVector = []
                self.nbr_clicks_Harm = 0
                print("HarmVector ="+str(self.HarmVector))
                self.H1.remove()
                self.H2.remove()
                print("lines =" +str(self.scopePlotAxis.lines))
                self.scopePlotCanvas.draw() 
            else: 
                x = event.xdata
                if self.nbr_clicks_Harm == 0:
                    self.H1 = self.scopePlotAxis.axvline(x,color='green')
                    self.scopePlotCanvas.draw()
                if self.nbr_clicks_Harm == 1:
                    self.H2 = self.scopePlotAxis.axvline(x,color='green')
                    self.scopePlotCanvas.draw()
                self.HarmVector.append(x)
                #self.scopePlotCanvas.draw()  
                self.nbr_clicks_Harm += 1
                self.HarmVector.sort()
                print("HarmVector ="+str(self.HarmVector))
                print("lines =" +str(self.scopePlotAxis.lines))


                
        if self.BGCheckBox.isChecked():
            if self.nbr_clicks_BG == 2:
                self.BGVector = []
                self.nbr_clicks_BG = 0
                print("BGVector ="+str(self.BGVector))
                self.BG1.remove()
                self.BG2.remove()
                print("lines =" +str(self.scopePlotAxis.lines))
                self.scopePlotCanvas.draw()                 
            else:
                x = event.xdata
                if self.nbr_clicks_BG == 0:
                    self.BG1 = self.scopePlotAxis.axvline(x,color='white')
                    self.scopePlotCanvas.draw()
                if self.nbr_clicks_BG == 1:
                    self.BG2 = self.scopePlotAxis.axvline(x,color='white')
                    self.scopePlotCanvas.draw()
                self.BGVector.append(x)
                #self.scopePlotCanvas.draw()  
                self.nbr_clicks_BG += 1  
                self.BGVector.sort()
                print("BGVector ="+str(self.BGVector))
                print("lines =" +str(self.scopePlotAxis.lines))
  
    def from_tof2int(self, tof1, tof2, delta_tof):
        return int((tof1 - tof2)/delta_tof)
        
        

    def tof2int(self, data):
        #returns SB, Harm and BG vectors with points in number of "pixels"

        print("TOF2INT")
        SB_tof1, SB_tof2 = self.SBVector[0], self.SBVector[1] 
        Harm_tof1, Harm_tof2 = self.HarmVector[0], self.HarmVector[1]
        BG_tof1, BG_tof2 = self.BGVector[0], self.BGVector[1]
        
        tof_min = data[0][0]
        tof_max = data[0][-1]

        nbrOfPoints = self.scopeWidget.reader.dataPointsNbr
        
        Delta_tof = abs((tof_max - tof_min)/nbrOfPoints)
        
        SB_i1 = self.from_tof2int(SB_tof1, tof_min, Delta_tof)
        SB_i2 = self.from_tof2int(SB_tof2, tof_min, Delta_tof)
    
        Harm_i1 = self.from_tof2int(Harm_tof1, tof_min, Delta_tof)
        Harm_i2 = self.from_tof2int(Harm_tof2, tof_min, Delta_tof)       
        
        BG_i1 = self.from_tof2int(BG_tof1, tof_min, Delta_tof)        
        BG_i2 = self.from_tof2int(BG_tof2, tof_min, Delta_tof)          
       
        #vectors containing the position of the edges of the bands, in int
        self.SBVector_points = [SB_i1, SB_i2]
        self.HarmVector_points = [Harm_i1, Harm_i2]
        self.BGVector_points = [BG_i1, BG_i2]