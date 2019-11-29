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
        
   
        
        self.scopePlotFigure = plt.Figure()
        self.scopePlotAxis = self.scopePlotFigure.add_subplot(111, facecolor='k')
        self.scopePlotCanvas = FigureCanvas(self.scopePlotFigure)          
        self.scopePlotCanvas.setMinimumWidth(250)
        self.scopePlotCanvas.setMinimumHeight(700)
        #self.scopePlotCanvas.setMaximumWidth(1000)
        self.scopePlotCanvas.setMaximumHeight(700)
       
        self.scopePlotTrace, = self.scopePlotAxis.plot([0,1],[0,0],color='yellow')
       
       
        
        
        box = QtWidgets.QHBoxLayout()
       
       
        winLayout = QtWidgets.QVBoxLayout()
        winLayout.addWidget(self.scopeWidget)
        winLayout.addWidget(self.stageWidget)
        winLayout.addWidget(self.scanWidget)
        winLayout.setSpacing(120)
        
        
        imageWidget = QtWidgets.QLabel()
        #imageWidget.setMaximumWidth(1000)
        pix = QPixmap('logo.png')
        scaledpix = pix.scaled(300,2000, QtCore.Qt.KeepAspectRatio)
        imageWidget.setPixmap(scaledpix)
        imageWidget.setParent(self)
        imageWidget.move(1150,620)
        
        emptywidget = QtWidgets.QLabel()
        
        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.scopePlotCanvas)
        rightLayout.addWidget(emptywidget)
        #rightLayout.addWidget(imageWidget)
        rightLayout.setSpacing(10)


        bottomLabel = QtWidgets.QLabel("SiRIUS (Stabilization of RABBIT Interferometer Using harmonic Sidebands) - ATTOLab - CEA - 2019")
        bottomLabel.setParent(self) 
        bottomLabel.move(1000,715)
        
        
        
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
        #print("x offset = "+str(x_offset))
        self.scopePlotCanvas.draw()    




       
       
    