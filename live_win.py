# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 11:14:36 2019

@author: mluttmann
"""





from PyQt5 import QtWidgets
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
        
       
       
        box.addLayout(winLayout)
        box.addWidget(self.scopePlotCanvas)
       
      
        self.setLayout(box)
        
        
        
        
        
   
    




       
       
    