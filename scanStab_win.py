# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 18:05:51 2019

@author: mluttmann
"""






from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from Rabbit_scan_stab import ScanStabWidget



#class scanStabTab(QtWidgets.QWidget):
class scanStabTab(QtWidgets.QWidget):
    def __init__(self, Tab3):
        """
        tab 4: scan stab Tab. Allows the user to perform a stabilized RABBIT scan.
        """
        super(scanStabTab, self).__init__(parent=None)
        
        self.tab3 =Tab3

        self.scanStabWidget = ScanStabWidget(self.tab3)
        
        
        
        
        box = QtWidgets.QHBoxLayout()
       
       
        winLayout=QtWidgets.QVBoxLayout()

        winLayout.addWidget(self.scanStabWidget)
        winLayout.setSpacing(120)
        
       
       
        box.addLayout(winLayout)
        #box.addWidget(self.scopePlotCanvas)
       
      
        self.setLayout(box)