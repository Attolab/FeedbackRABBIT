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
from SmarAct_f import StageWidget
from Rabbit_scan import ScanWidget, ScanningLoop


import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar



class RABBIT_feedback(QtWidgets.QTabWidget):
    def __init__(self, parent = None):
        super(RABBIT_feedback, self).__init__(parent)
    
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()
        self.tab3 = QtWidgets.QWidget()
      
        self.scopeWidget = ScopeWidget()
        self.stageWidget = StageWidget()
        self.scanWidget = ScanWidget()
    		
       
        self.addTab(self.tab1,"Live")
        self.addTab(self.tab2,"Sidebands")
        self.addTab(self.tab3,"Feedback")
        
        self.scan_step= (self.scanWidget.stopPosSpinBox.value()- self.scanWidget.startPosSpinBox.value())/self.scanWidget.nbrPointsSpinBox.value()
        
        #print(self.scan_step)
        self.rabbit_mat = None
        
        self.data_x=[]
        #self.rabbit_t=[]
        self.int_SB1=[]
        self.int_SB2=[]
        
        self.fit_SB1=[]
        self.fit_SB2=[]

        self.O1=0.
        self.O2=0.
        self.A1=0.
        self.A2=0.
        self.dphi=0.
        
       
        self.LiveUI()
        self.SidebandsUI()
        self.FeedbackUI()
        self.setWindowTitle("RABBIT feedback")
        self.setWindowIcon(QIcon("lapin.png") )
      
        self.setGeometry(100, 100, 1500, 1000)
        #self.statusBar().showMessage("Statusbar - awaiting user control")
        self.show()
      
    		
        
    #####################################################Layout########################################################
		
    def LiveUI(self):
      
       
       
       
       
       
        # create the figure and the figure navigation
       self.scopePlotFigure = plt.Figure()
       self.scopePlotAxis = self.scopePlotFigure.add_subplot(111, facecolor='k')
#            self.axis.axis('auto')
       self.scopePlotCanvas = FigureCanvas(self.scopePlotFigure)             # Canvas Widget that displays the figure
       self.scopePlotCanvas.setMinimumWidth(250)
       self.scopePlotCanvas.setMinimumHeight(500)
       self.scopePlotCanvas.setMaximumWidth(1000)
       self.scopePlotCanvas.setMaximumHeight(700)
       
       self.scopePlotTrace, = self.scopePlotAxis.plot([0,1],[0,0],color='yellow')
       #self.toolbar = NavigationToolbar(self.scopePlotCanvas, self) # Navigation widget
        # add the figure and the figure navigation to the figure layout
       #self.scopePlotLayout.addWidget(self.toolbar)
       
     
        # add the figure layout to the main layout
       #self.tab2.setLayout(self.scopePlotLayout)
       
       box = QtWidgets.QHBoxLayout()
       
       
       winLayout=QtWidgets.QVBoxLayout()
       winLayout.addWidget(self.scopeWidget)
       winLayout.addWidget(self.stageWidget)
       winLayout.addWidget(self.scanWidget)
       winLayout.setSpacing(120)
       
       
       box.addLayout(winLayout)
       box.addWidget(self.scopePlotCanvas)
       
       #box.addWidget(self.scopePlotCanvas,0,1)
       self.tab1.setLayout(box)
       
       
       
       
       """
       main window creationand design
       """
       # setup menu bar
       #self.statusBar()
       #self.menuBar = self.menuBar()
       #self.applicationMenu = self.menuBar.addMenu('Application')
       # create a quit action
       #self.quitAction = QtWidgets.QAction('Quit', self)
       #self.quitAction.setShortcut('Ctrl+Q')
       #self.quitAction.setStatusTip('Exit application')
       #self.quitAction.triggered.connect(self.close)
       # Add actions to the menubar
       #self.applicationMenu.addAction(self.quitAction)
    
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
        # create the figure and the figure navigation
        self.scanPlotFigure = plt.Figure()
        self.scanPlotAxis = self.scanPlotFigure.add_subplot(111)
#            self.axis.axis('auto')
        self.scanPlotCanvas = FigureCanvas(self.scanPlotFigure)             # Canvas Widget that displays the figure
        self.scanPlotCanvas.setMinimumWidth(700)
        self.scanPlotCanvas.setMinimumHeight(500)
        #self.scanPlotCanvas.setMaximumWidth(800)
        #self.scanPlotCanvas.setMaximumHeight(700)
       
        self.scanPlotTrace = self.scanPlotAxis.matshow([[0,0],[0,0]])
        #self.toolbar = NavigationToolbar(self.scopePlotCanvas, self) # Navigation widget
         # add the figure and the figure navigation to the figure layout
        #self.scopePlotLayout.addWidget(self.toolbar)
        self.scanPlotLayout.addWidget(self.scanPlotCanvas)
        # add the figure layout to the main layout
        #self.tab2.setLayout(self.scopePlotLayout)
        
        self.n=1
        
        self.SB_vector=[]
        self.nbr_clicks=0
        
        
        self.scan_step= (self.scanWidget.stopPosSpinBox.value()- self.scanWidget.startPosSpinBox.value())/self.scanWidget.nbrPointsSpinBox.value()
        self.scan_step= 20.
        
        
        
        
        
        self.SBPlotLayout = QtWidgets.QVBoxLayout()
        # create the figure and the figure navigation
        self.SBPlotFigure = plt.Figure()
        self.SBPlotAxis = self.SBPlotFigure.add_subplot(111)
#            self.axis.axis('auto')
        self.SBPlotCanvas = FigureCanvas(self.SBPlotFigure)             # Canvas Widget that displays the figure
        #self.SBPlotCanvas.setMaximumWidth(500)
        #self.SBPlotCanvas.setMaximumHeight(200)
        #self.SBPlotCanvas.setMinimumHeight(200)
        
        #self.SBPlotTrace, = self.SBPlotAxis.plot([0,1],[0,0])
        #self.toolbar = NavigationToolbar(self.SBPlotCanvas, self) # Navigation widget
        # add the figure and the figure navigation to the figure layout
        #self.SBPlotLayout.addWidget(self.toolbar)
        self.SBPlotLayout.addWidget(self.SBPlotCanvas)
        # add the figure layout to the main layout
        self.SBPlotAxis.clear()
        
        
        self.horPlotLayout = QtWidgets.QVBoxLayout()
        # create the figure and the figure navigation
        self.horPlotFigure = plt.Figure()
        self.horPlotAxis = self.horPlotFigure.add_subplot(111)
        
#            self.axis.axis('auto')
        self.horPlotCanvas = FigureCanvas(self.horPlotFigure)             # Canvas Widget that displays the figure
        #self.horPlotCanvas.setMaximumWidth(500)
        #self.horPlotCanvas.setMinimumHeight(100)
        #self.SBPlotCanvas.setMaximumHeight(350)
        
        #self.SBPlotTrace, = self.SBPlotAxis.plot([0,1],[0,0])
        #self.toolbar = NavigationToolbar(self.SBPlotCanvas, self) # Navigation widget
        # add the figure and the figure navigation to the figure layout
        #self.SBPlotLayout.addWidget(self.toolbar)
        self.horPlotLayout.addWidget(self.horPlotCanvas)
        # add the figure layout to the main layout
        self.horPlotAxis.clear()
        
        
        self.errorPlotLayout = QtWidgets.QVBoxLayout()
        # create the figure and the figure navigation
        self.errorPlotFigure = plt.Figure()
        self.errorPlotAxis = self.errorPlotFigure.add_subplot(111)
#            self.axis.axis('auto')
        self.errorPlotCanvas = FigureCanvas(self.errorPlotFigure)             # Canvas Widget that displays the figure
        
        self.errorPlotLayout.addWidget(self.errorPlotCanvas)
        # add the figure layout to the main layout
        self.errorPlotAxis.clear()
        
        
        
        
        
       
        
        self.importdata_btn = QtWidgets.QPushButton("Load RABBIT scan", self)
        self.importdata_btn.clicked.connect(self.import_scan)
        self.importdata_btn.setMaximumWidth(150)
        
        
        
        
        #self.select_bands_btn=QtWidgets.QPushButton("Select sidebands", self)
        
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
        #self.O1_display.returnPressed.connect(self.update_envect_fn)
        
        box2 = QtWidgets.QGridLayout()
        box2.setSpacing(10)
        #box2.addWidget(self.importdata_btn,0,0)
        #box2.addWidget(self.SB_plot_btn,0,1)
        #box2.addWidget(self.horizontal_plot_btn,3,0)
        #box2.addWidget(self.error_plot_btn,4,1)
        
        
        #box2.addWidget(self.O1_display,3,1)
        #box2.addWidget(QtWidgets.QLabel("Offset 1"), 4,1)
        
        
        ########################
        
        scanLayout=QtWidgets.QGridLayout()
        scanLayout.addWidget(self.importdata_btn,0,0)
        scanLayout.addWidget(self.scanPlotCanvas,1,0)
        scanLayout.addWidget(self.horizontal_plot_btn,2,0)
        scanLayout.addWidget(self.horPlotCanvas,3,0)
        #box2.addWidget(self.scanPlotCanvas,2,0)
        #box2.addWidget(self.SBPlotCanvas,2,1)
        #box2.addWidget(self.horPlotCanvas,4,0)
        #box2.addWidget(self.errorPlotCanvas,5,1)
        #box2.addWidget(NavigationToolbar(self.scanPlotCanvas, self))
        
        box2.addLayout(scanLayout,0,0)
        
        #########################
        
        signalLayout=QtWidgets.QGridLayout()
        signalLayout.addWidget(self.SB_plot_btn, 0, 0)
        signalLayout.addWidget(self.SBPlotCanvas, 1, 0)
        
       
        
        
        
        #param_box=QtWidgets.QGroupBox()
        paramLayout = QtWidgets.QGridLayout()
        
        
        #param_box.setTitle("Sidebands parameters")
        #param_box.setSizePolicy(200, 200)
        
        #paramLayout.addWidget(param_box)
        
        
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
        
        
        #errorLayout = QtWidgets.QGridLayout()
        
        #errorLayout.addWidget(self.error_plot_btn,0,0)
        #errorLayout.addWidget(self.errorPlotCanvas,1,0)
        signalLayout.addLayout(paramLayout,2,0)
        
        signalLayout.addWidget(self.error_plot_btn, 3, 0)
        signalLayout.addWidget(self.errorPlotCanvas, 4, 0)
        #param_box.setLayout(paramLayout)
        box2.addLayout(signalLayout,0,1)
        #box2.addLayout(paramLayout,3,1)
        self.tab2.setLayout(box2)
        
        
        
      
      		
    def FeedbackUI(self):
        
        
        #scope=self.scopePlotCanvas
        
        self.launch_feedback_btn= QtWidgets.QPushButton("LAUNCH RABBIT \n FEEDBACK", self)
        
        self.launch_feedback_btn.setMaximumWidth(200)
        #♠self.launch_feedback_btn.setMinimumHeight(500)
        self.launch_feedback_btn.setCheckable(True)
        self.launch_feedback_btn.setIcon(QIcon('lapin.png'))
        self.launch_feedback_btn.setIconSize(QtCore.QSize(75,75))
        self.launch_feedback_btn.setFont(QFont('SansSerif', 10))
        
        
        
        
        displayLayout = QtWidgets.QVBoxLayout()
        
        #displayLayout.addWidget(scope)
        
        
        
        
        
        interactLayout = QtWidgets.QVBoxLayout()
        interactLayout.addWidget(self.launch_feedback_btn)
        
        box3 = QtWidgets.QHBoxLayout()
        box3.addLayout(displayLayout)
        box3.addLayout(interactLayout)
        
        
        
      
        self.tab3.setLayout(box3)
        
        
        
        
        
        
        #############################################################################functions###############################
      
        ################### Live-functions #################################
      
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
       self.scopePlotAxis.set_ylabel("Tension (V)", fontsize=17)
       self.scopePlotAxis.set_xlabel("Time (s)", fontsize=17)
       
       self.scopePlotCanvas.draw()
       
      
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
        #self.TwoDPlotDraw(data)
    
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
            self.scopeWidget.triggerModeComboBox.setCurrentIndex(3)
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
        self.scanningLoop.setScopeMode.connect(self.scopeWidget.triggerModeComboBox.setCurrentIndex)
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
            
            
            
            
            
            
        ################### Sidebands-functions #################################
        
  
    
    
    
    def import_scan(self):
       
        data_f = QtWidgets.QFileDialog.getOpenFileName(self, 'Import RABBIT scan')
        data_filename = data_f[0]
        
        if (data_filename):
            fdir, fname = os.path.split(data_filename)
            fdir = fdir + '/'
            flist = glob(fdir + '*[0-9][0-9][0-9][0-9].txt')
            #flist contains the list of paths to all spectrum files
            #print(flist)
            self.n=len(flist)
            
            #print(flist[0])
           
            #n_t=len(self.import_spectrum(flist[0]))
            list_t=self.import_spectrum(flist[0])[0]
            n_t=len(list_t)
            
            #print(list_t)
            RABBIT_array=np.zeros(shape=(self.n,n_t))
            
            for i in range(self.n):
                RABBIT_array[i]=self.import_spectrum(flist[i])[1]
           
            #print(RABBIT_array, list_t)
            self.rabbit_mat=RABBIT_array
            self.rabbit_t=list_t
            
            
            #self.scanPlotTrace.set_array(self.rabbit_mat)
            self.scanPlotTrace = self.scanPlotAxis.matshow(self.rabbit_mat)
            self.scanPlotAxis.set_aspect('auto')
            self.scanPlotAxis.set_ylabel("Delay", fontsize=12)
            self.scanPlotAxis.set_xlabel("ToF", fontsize=12)
            self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan", fontsize=8)
            
            
            self.scanPlotCanvas.draw()
            
            self.cid = self.scanPlotCanvas.mpl_connect('button_press_event', self)
            
      
    def __call__(self, event):
            if self.nbr_clicks<=4:
                #print('click', event)
                #if event.inaxes!=self.line.axes: return
                
                #self.xs.append(event.xdata)
                #self.ys.append(event.ydata)
                if self.nbr_clicks==4:
                    self.SB_vector=[]
                    self.nbr_clicks+=1
                    #print(self.SB_vector)
                else:
                    
                    self.scanPlotAxis.axvline(x=event.xdata,color='red')
                    self.SB_vector.append(event.xdata)
                    #print(self.SB_vector)
                    self.scanPlotCanvas.draw()
                    self.nbr_clicks+=1
                    self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan", fontsize=8)
            if self.nbr_clicks>4:
                self.SB_vector=[]
                self.scanPlotAxis.clear()
                self.scanPlotTrace = self.scanPlotAxis.matshow(self.rabbit_mat)
                self.scanPlotAxis.set_title("Select two sidebands in phase quadrature by clicking on the scan", fontsize=8)
                self.scanPlotAxis.set_aspect('auto')
                self.scanPlotAxis.set_ylabel("Delay", fontsize=16)
                self.scanPlotAxis.set_xlabel("ToF", fontsize=16)
                self.scanPlotCanvas.draw()
                self.nbr_clicks=0
                
                
            
            
            

    def import_spectrum(self, filename):
        file=open(filename, 'r')
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
        x_data=[]
        y_data=[]
        for elt in data_array:
            x_data.append(elt[0])
            y_data.append(elt[1])
    
    
        return [x_data,y_data]
        
       
    def cosine(self, x, O, A, phi):
        self.scan_step=20.
        tau_step=self.scan_step/(3*10**17)
        #print(self.scan_step)
        
        w=(2.35*10**15)*tau_step  #laser frequency with step units
        return O+A*np.cos(4*w*x+phi)
    
    def lin_fit(self, x, a, b):
        return a*x+b
    
    
    def SBPlotDraw(self):
        self.SBPlotAxis.clear()
        # first integrate
        
        self.int_SB1=[]
        self.int_SB2=[]
        
        self.fit_SB1=[]
        self.fit_SB2=[]
        
        SB_vector_int=[]
        
        for elt in self.SB_vector:
            SB_vector_int.append(int(elt))
        SB_vector_int.sort()
        for i in range(2):
            if i==0:  # first sideband
                int_left=SB_vector_int[0]
                int_right=SB_vector_int[1]
                width=int_right-int_left
                for i in range(self.n):
                    self.int_SB1.append(np.trapz(self.rabbit_mat[i][int_left:int_right])/width)
            if i==1:  #2nd sideband
                int_left=SB_vector_int[2]
                int_right=SB_vector_int[3]
                width=int_right-int_left
                for i in range(self.n):
                    self.int_SB2.append(np.trapz(self.rabbit_mat[i][int_left:int_right])/width)
        
        
        self.data_x=np.linspace(0, self.n, self.n)
        
        # fit
        params1, cov1 = optimize.curve_fit(self.cosine, self.data_x, self.int_SB1)
        
        
        self.O1=params1[0]
        self.A1=params1[1]
        
        
        params2, cov2 = optimize.curve_fit(self.cosine, self.data_x, self.int_SB2)
        self.O2=params2[0]
        self.A2=params2[1]
        
        self.dphi=params1[2]-params2[2]
        
        
        
        for i in range(self.n):
            self.fit_SB1.append(self.cosine(self.data_x[i], params1[0], params1[1], params1[2]))
            self.fit_SB2.append(self.cosine(self.data_x[i], params2[0], params2[1], params2[2]))
        
        #self.fit_SB1=self.cosine(data_x, params1[0], params1[1], params1[2])
        #self.fit_SB2=self.cosine(data_x, params2[0], params2[1], params2[2])
        
        
        # then plot
        
        #plot integrated sidebands 
        
        self.SBPlotAxis.plot(self.data_x, self.int_SB1, label='SB1')
        self.SBPlotAxis.plot(self.data_x, self.int_SB2, label='SB2')
        
        
        
        
        #plot fitted sidebands 
        self.SBPlotAxis.plot(self.data_x, self.cosine(self.data_x, params1[0], params1[1], params1[2]), label="Fit SB1")#, params1[3]))
        self.SBPlotAxis.plot(self.data_x, self.cosine(self.data_x, params2[0], params2[1], params2[2]), label="Fit SB2")#, params2[3]))
        self.SBPlotAxis.set_ylabel("Signal (V)", fontsize=10)
        self.SBPlotAxis.set_xlabel("Delay", fontsize=10)
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
        list_error=[]
        list_error_fit=[]
        list_error=np.unwrap(np.arctan2(
            (self.int_SB1 - self.O1)/self.A1,
            (self.int_SB2 - self.O2)/self.A2
        ))
        list_error_fit=np.unwrap(np.arctan2(
            (self.fit_SB1 - self.O1)/self.A1,
            (self.fit_SB2 - self.O2)/self.A2
        ))
        
        param_lin, cov = optimize.curve_fit(self.lin_fit, self.data_x, list_error)
        
        
            
        self.errorPlotAxis.plot(self.data_x, list_error, label= "Error signal")
        self.errorPlotAxis.plot(self.data_x, list_error_fit, 'k--', label="Error signal extracted from cosine fit", )
        self.errorPlotAxis.plot(self.data_x, self.lin_fit(self.data_x, param_lin[0], param_lin[1]), label= "Linear fit of the error signal")
        #self.errorPlotAxis.set_title("Error signal", fontsize=8)
        self.errorPlotAxis.set_ylabel("Error signal", fontsize=10)
        self.errorPlotAxis.set_xlabel("Delay", fontsize=10)
        self.errorPlotAxis.legend(loc='best')
        self.errorPlotCanvas.draw()
    
    
    
    
        ################### Feedback-functions #################################
    
     


def main():
   print(QtWidgets.QStyleFactory.keys())
   app = QtWidgets.QApplication(sys.argv)
   #app.aboutToQuit.connect(app.deleteLater)
   app.setStyle('Fusion')
   ex = RABBIT_feedback()
   ex.show()
   
   sys.exit(app.exec_())
   #raise Exception('exit')
   #sys.exit(0)
   #app.quit()
	
if __name__ == '__main__':
   main()
  