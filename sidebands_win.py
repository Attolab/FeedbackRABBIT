# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 11:33:42 2019

@author: mluttmann
"""
import sys
import os





import traceback
from glob import glob


from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


import numpy as np
from scipy import optimize





class SidebandsTab(QtWidgets.QWidget):
    def __init__(self,  parent=None):
        """
        tab
        """
        super(SidebandsTab, self).__init__(parent=None)
        
        self.omega = 2.35*10**(15)  #IR laser pulsation in rad/s
        self.c_m_s = 3*10**8  #speed of light
        self.scan_step = 20.  #scan step in nm
        self.rabbit_mat = None  #this array will contain the RABBIT scan
        
        self.n = 1
        self.SB_vector = []
        self.nbr_clicks = 0
        
        self.scan_step = 20.
        
        self.data_x = []  #list of delay values in number of steps     
        self.SB_vector_int = []  #sidebands positions on the scan array (integers, in scan steps)
        self.BG_vector = []   #background band vectorthat will be substracted from sidebands
        
        self.int_SB1 = []  #intergrated sideband 
        self.int_SB2 = []
        
        self.int_offset = []  #offset obtained by intergrating the background band
        
        self.retrieved_SB1 = []  #sideband with background removed
        self.retrieved_SB2 = []
        
        self.fit_SB1 = []  #cosine fit of sidebands
        self.fit_SB2 = []


        
        self.data_x_nm=[]  #list of delay values converted in nm
        self.list_error = []   #error signal extracted from the parameters above (O1, O2, A1, A2, etc.) 
        
        self.O1 = 0.  #offset of the fitted sideband
        self.O2 = 0.  #amplitude of the fitted  sideband
        self.A1 = 0.
        self.A2 = 0.
        self.dphi = 0.  #phase shift between the two fitted sidebands (we want it to be close to pi/2)
        

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
        
        
        self.importdata_btn = QtWidgets.QPushButton("Load self scan", self)
        self.importdata_btn.clicked.connect(self.import_scan)
        self.importdata_btn.setMaximumWidth(130)
        
        
        self.SB_plot_btn = QtWidgets.QPushButton("Plot sidebands", self)
        self.SB_plot_btn.clicked.connect(self.SBPlotDraw)
        self.SB_plot_btn.setMaximumWidth(90)
        
        
        self.horizontal_plot_btn = QtWidgets.QPushButton("Plot horizontal cross-section", self)
        self.horizontal_plot_btn.clicked.connect(self.horPlotDraw)
        self.horizontal_plot_btn.setMaximumWidth(145)
        
        
        self.error_plot_btn = QtWidgets.QPushButton("Plot error signal", self)
        self.error_plot_btn.clicked.connect(self.errorPlotDraw)
        self.error_plot_btn.setMaximumWidth(100)
        
        
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
        
            
    
      
        self.setLayout(box2)
        
        
        
        
        
    def import_scan(self):
   
        data_f = QtWidgets.QFileDialog.getOpenFileName(self, 'Import self scan')
        data_filename = data_f[0]
        
        if (data_filename):
            fdir, fname = os.path.split(data_filename)
            fdir = fdir + '/'
            flist = glob(fdir + '*[0-9][0-9][0-9][0-9].txt')
            #flist contains the list of paths to all spectrum files
           
            self.n = len(flist)
           
            list_t = self.import_spectrum(flist[0])[0]
            n_t = len(list_t)
         
            self_array = np.zeros(shape=(self.n,n_t))
            
            for i in range(self.n):
                self_array[i] = self.import_spectrum(flist[i])[1]
           
            self.self_mat = self_array
            self.self_t = list_t
            
            self.scanPlotTrace = self.scanPlotAxis.matshow(self.self_mat)
            self.scanPlotAxis.set_aspect('auto')
            self.scanPlotAxis.set_ylabel("Delay", fontsize=10)
            self.scanPlotAxis.set_xlabel("ToF", fontsize=10)
            self.scanPlotAxis.set_title("Select two sidebands (in red) in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
            
            
            self.scanPlotCanvas.draw()
            
            self.scanPlotCanvas.mpl_connect('button_press_event', self.onclick)
            
      
    def onclick(self, event):
        
        if self.nbr_clicks<=6:
           
            if self.nbr_clicks>=4:
                self.scanPlotAxis.axvline(x=event.xdata,color='black')
                self.BG_vector.append(event.xdata)
                self.scanPlotCanvas.draw()
                #self.scope2PlotCanvas.draw()
                self.nbr_clicks += 1
                
            else:
                self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
                    
                self.scanPlotAxis.axvline(x=event.xdata,color='red')
                #self.scope2PlotAxis.axvline(x=self.self_t[int(event.xdata)],color='red')  #second view of the scope
                self.SB_vector.append(event.xdata)
                
                self.scanPlotCanvas.draw()
                
                #self.scope2PlotCanvas.draw()
                self.nbr_clicks+=1
                self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
        if self.nbr_clicks>6:
            self.SB_vector = []
            self.BG_vector = []
            self.scanPlotAxis.clear()
            self.scanPlotTrace = self.scanPlotAxis.matshow(self.self_mat)
            self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan \n Also select a band to retrieve the background jitter (in black)", fontsize=8)
            self.scanPlotAxis.set_aspect('auto')
            self.scanPlotAxis.set_ylabel("Delay (steps)", fontsize=16)
            self.scanPlotAxis.set_xlabel("ToF", fontsize=16)
            self.scanPlotCanvas.draw()
            self.nbr_clicks=0
       
            
            
            
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
        #print(self.SB_vector)
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
                    self.int_SB1.append(np.trapz(self.self_mat[i][int_left:int_right])/width)
            if i==1:  #2nd sideband
                int_left = self.SB_vector_int[2]
                int_right = self.SB_vector_int[3]
                width = int_right-int_left
                for i in range(self.n):
                    self.int_SB2.append(np.trapz(self.self_mat[i][int_left:int_right])/width)
                    
            if i==2:  #3rd sideband
                int_left = self.BG_vector_int[0]
                int_right = self.BG_vector_int[1]
                width = int_right-int_left
                for i in range(self.n):
                    integral=np.trapz(self.self_mat[i][int_left:int_right])/width
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
        self.horPlotAxis.plot(self.self_mat[0])
        self.horPlotAxis.set_title("ToF signal at first step", fontsize=8)
        self.horPlotAxis.set_ylabel("Signal (V)", fontsize=10)
        self.horPlotAxis.set_xlabel("ToF", fontsize=10)
        self.horPlotAxis.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        self.horPlotCanvas.draw()
        
    
    def errorPlotDraw(self):
        
        self.errorPlotAxis.clear()
        self.list_error = []
        '''
        list_error_fit = []
        self.list_error = np.unwrap(np.arctan2(
            (self.retrieved_SB1 - self.O1)/self.A1,
            (self.retrieved_SB2 - self.O2)/self.A2
        ))
        list_error_fit = np.unwrap(np.arctan2(
            (self.fit_SB1 - self.O1)/self.A1,
            (self.fit_SB2 - self.O2)/self.A2
        ))
        '''
        
        list_error_fit = []
        self.list_error = np.arctan2(
            (self.retrieved_SB1 - self.O1)/self.A1,
            (self.retrieved_SB2 - self.O2)/self.A2
        )
        list_error_fit = np.arctan2(
            (self.fit_SB1 - self.O1)/self.A1,
            (self.fit_SB2 - self.O2)/self.A2
        )
        
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
        
