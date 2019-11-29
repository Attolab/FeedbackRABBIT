
# -*- coding: utf-8 -*-
"""
LeCroy WaveRunner 625Zi oscilloscope
The first Class loops over a scope reading procedure. It is controlled by the second one.
The second class is the main scope controlling widget, concentrating on the 
if main: this python script includes the widget in a window and adds a menu to it
"""
import sys
#import ctypes

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QIcon

import win32com.client #imports the pywin32 library, this library allow the control of other applications (used here for LeCroy.ActiveDSOCtrl.1)

import matplotlib.pyplot as plt
# allow the placement of matlpotlib canvas on a Qt interface :
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# allow the placement of matlpotlib plotting tool on a Qt interface :
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# TODO :
# 0) set tempo of reading loops AND test different speeds
# 1) Replace the elif cases by a dictionnary in the Run function of the ScopeReader class
# 2) Optimize the start up procedure (ScopeGroupBoxToggled function) and clean the thread().msleep(???) calls
# 3) ?crash due to 'No Data Available' on a channel?
#     The the line waveform = self.scope.GetScaledWaveformWithTimes(self.channel, 5000, 0) inside the ReadWaveform function is the oigin of the crash...
# 4) ?transfert the data integration completion control on the oscilloscope side? (cf maui-remote-control-and-automation-manual.pdf p178)

"""
Scope reading class
!!! the communication only works if the adress is properly declared in the self.scope.MakeConnection(USBadress) method
AND the scope menu : utilities>utilities setup...>remote menu is set to USBTMC
"""
class ScopeReader(QtCore.QObject):
    # Signals emitted by the ScopeReader class
    dataRecieved = QtCore.pyqtSignal(tuple)
    readerUpdate = QtCore.pyqtSignal(list)

    def __init__(self, scopeWidget, scopeHandle):
        super(ScopeReader, self).__init__()
        self.scope = scopeHandle
        self.mode = "Starting"
        # variable containing the channel currently selected in the ScopeWidget
        self.channel = "C1"
        # initiallize the integer containing the number of data points to read from the scope at the value displayed on the user interface
        self.dataPointsNbr = scopeWidget.dataPointsNbrSpinBox.value()
        
        # connect the writeReader signal from the holding scope widget to the writeScope function of this class
        scopeWidget.writeReader.connect(self.writeScope)
        
        self.period = 0.1*1000  #period of queries, in millisecond
        
        
        self.canAsk = True

    def writeScope(self, command):
        #print(command)
        if command[0:3] =="VBS":
            # send command
            self.scope.WriteString(command, 1)
            variable =  command.split("'")[1].split(".")[-1]    # get the last part of the command (variable name and the value in the case the command is not a querry)
            if command[3] == "?": # if the command is a query...
                value = self.scope.ReadString(50) # read the instrument reply
                if value != 'No Data Available':
                    self.readerUpdate.emit([variable, value]) # and send it as a list containing the variable and it's new value
                if variable == "TriggerMode": # if the query is the trigger mode ...
                    # ... the value is stored in the ScopeReader widget 
                    self.mode = value
            elif variable.split("=")[0] == "TriggerMode": # if the command is send to set a new trigger mode ...
                value = variable.split('"')[-2]
                # ... the new value is stored in the ScopeReader widget 
                self.mode = value
                
    def selectChannel(self, channel):
        # CAUTION!!! we get a python crash each time a is channel unproperly (???meaning???) set on the oscilloscope is selected (reasons???) 
        self.channel = channel
    
    def SetDataPointsNbr(self, nbr):
        self.dataPointsNbr = nbr

    def ReadWaveform(self):
        # update the sweep value recorded in the progress bar
        self.writeScope("""VBS? 'return=app.Acquisition.""" + """C""" + self.channel[1] +""".Out.Result.Sweeps' """)
        # read the waveform
        waveform = self.scope.GetScaledWaveformWithTimes(self.channel, self.dataPointsNbr, 0)
        #if len(waveform[0]) > 1:
        if waveform != None:
            if len(waveform[0]) > 1:
            # emit non-emtpy data only
                self.dataRecieved.emit(waveform)
    #######################################################################################        
    def ReadParameters(self):
        #update parameters such as Verscale, Horscale, etc.....
        self.writeScope("""VBS? 'return=app.Acquisition.""" + """C""" + self.channel[1] + """.VerScale' """)
        self.writeScope("""VBS? 'return=app.Acquisition.Horizontal.HorScale'""")
       
        self.writeScope("""VBS? 'return=app.Acquisition.""" + """C""" + self.channel[1] + """.Out.Result.VerticalOffset' """)
        self.writeScope("""VBS? 'return=app.Acquisition.""" + """C""" + self.channel[1] + """.Out.Result.HorizontalOffset' """) 
        
    

    def Run(self):
#        print("start main loop")
        # start scope procedure
        self.scope.MakeConnection("USBTMC:USB0::0x05ff::0x1023::2816N63086::INSTR")
        print("after make connection")
#        self.scope.DeviceClear(True)     How should I clear the scope communication channel without restarting it????
        remote = self.scope.SetRemoteLocal(1)
        # Wating for the completion of "ReadScopeState"
        # "ReadScopeState" returns the trigger mode, which is then used here to switch to the propper function
#        modesDictionary = {"Auto":self.Auto(),
#                           "Normal":self.Normal(),
#                           "Single":self.Single(),
#                           "Stop":self.Stop(),
#                           "Starting":""}
        while self.mode: # An unempty string is considered True in python
            self.thread().msleep(100)
            if self.mode == "Auto":
                self.Auto()
            elif self.mode == "Normal":
                self.Normal()
            elif self.mode == "Single":
                self.Single()
            elif self.mode == "Stop":
                self.Stop()
        # stop scope communication
        self.scope.SetRemoteLocal(0)
        print("exit main loop")

    def Auto(self):
        while self.mode == "Auto":
            self.ReadWaveform()
            self.ReadParameters()
            # pause loop
            self.thread().msleep(self.period)

    def Normal(self):
        while self.mode == "Normal":
            
            if self.canAsk == True:
                #print("allow VBS? command for new scope data")
                self.ReadWaveform()
                self.ReadParameters()
            # pause loop
                
            #else:
                #print("VBS? command forbidden")
                
            self.thread().msleep(self.period)
            self.canAsk = True
    def Single(self):
        # make a single acquisition before switching to the stopped state when the oscilloscope is ready.
        self.ReadWaveform()
        self.ReadParameters()
        while self.mode == "Single":
            # pause loop
            self.writeScope("""VBS? 'return=app.Acquisition.TriggerMode' """)
            self.thread().msleep(self.period)

    def Stop(self):
        # Wait for the user to switch to an other trigger mode
        while self.mode == "Stop":
            self.thread().msleep(self.period)
        
    def Off(self):
        self.mode = ""



"""
Scope widget class
"""
qtCreatorFile = "ScopePyQtUI_f.ui"
Ui_ScopeWidget, QtBaseClass = loadUiType(qtCreatorFile)
class ScopeWidget(QtWidgets.QFrame, Ui_ScopeWidget):
    # Create a signal called 'writeReader' to send string to the scope through the scopeReader class
    writeReader = QtCore.pyqtSignal(str)
    emitData = QtCore.pyqtSignal(tuple) # the scopeWidget is not working with the data and just transmit them with this signal
    alertMessage = QtCore.pyqtSignal(str) # create an alert signal for inproper communication with the scope

    def __init__(self, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setupUi(self)
        self.scope=win32com.client.Dispatch("LeCroy.ActiveDSOCtrl.1")
        self.YScale = 0.01
        self.XScale = 5.
        self.YOffset = 0.
        self.XOffset = 0.
        # connect group box to start/stop procedure
        self.scopeGroupBox.toggled.connect(self.ScopeGroupBoxToggled)
        print("Connect Group Box")
    def UIUpdate(self, updatedData):
        #print(updatedData)
        if not updatedData[1]: # alert the user if the data string is empty
            self.alertMessage.emit(updatedData[0] + " variable not recieved, there may be a communication problem with the scope.")
            print("updatedata = ")
            print(updatedData[1])
        else: # update UI only if the data string is not empty
            if updatedData[0] == "VerticalOffset":
                
                self.YOffset=float(updatedData[1])
                
                self.OffsetLCD.blockSignals(True)
                self.OffsetLCD.display(-float(updatedData[1]))
                self.OffsetLCD.blockSignals(False)
                #print("YOffset="+str(self.YOffset))
                
            elif updatedData[0] == "HorizontalOffset":
                self.XOffset=float(updatedData[1])
             
            elif updatedData[0] == "VerScale":           
                self.YScale=float(updatedData[1])
                #print("Verscale="+str(self.YScale))
         
            elif updatedData[0] == "AverageSweeps":
                value = int(updatedData[1])
                self.sweepsProgressBar.setMaximum(value)
                
            elif updatedData[0] == "Sweeps":
                value = int(updatedData[1])
                value = min(self.sweepsProgressBar.maximum(), value)
                self.sweepsProgressBar.setValue(value)
            elif updatedData[0] == "HorScale":
                self.XScale=float(updatedData[1])
                #print("Horscale="+str(self.XScale))
  

    def ScopeGroupBoxToggled(self):
        if self.scopeGroupBox.isChecked():
            # create the scope reader instance
            self.reader = ScopeReader(self, self.scope)
            # connect the scope reader 'readerUpdate' signal to UIUpdate mehod
            self.reader.readerUpdate.connect(self.UIUpdate)


            # create the scope reader thread and move the reader instance to that thread
            self.readerThread = QtCore.QThread()
            self.reader.moveToThread(self.readerThread)
            self.readerThread.started.connect(self.reader.Run)
            print("after Run")
            # start the reader thread...
            self.readerThread.start()
            # ... and wait for it to be running (tests indicate that this safety is useless!)
            while not self.readerThread.isRunning():
                self.thread().msleep(100)
            
            # wait for the reader Run method to be started before launching the self.ReadScopeState method
            self.thread().msleep(1000)
            # read the oscilloscope state and set the widget interface buttons accordingly
            self.ReadScopeState()

            self.ConnectButtons()
            self.scopeGroupBox.setTitle("ON")
        else:
            self.reader.Off()
            
            self.readerThread.started.disconnect()
            self.DisconnectButtons()
            self.readerThread.exit()
            # wait for the thread exit before going on :
            while self.readerThread.isRunning():
                self.thread().msleep(100)

            self.scopeGroupBox.setTitle("OFF")

    def ReadScopeState(self):
        self.ChannelSelect()
        self.GetCoupling()
        self.GetTScale()
        self.GetSampleMode()
        self.GetNbrOfSequence()
        self.GetTriggerMode()
        
       

    def ConnectButtons(self):
        # connect the reader.dataRecieved signal to he scopeWidget.emitData signal
        self.reader.dataRecieved.connect(self.TransmitData)
        
        # connect controls to functions
        self.channelComboBox.currentIndexChanged.connect(self.ChannelSelect)
        self.dataPointsNbrSpinBox.valueChanged.connect(self.DataPointsNbrChanged)
      
    def DisconnectButtons(self):
        # disconnect the reader.dataRecieved signal to he scopeWidget.emitData signal
        self.reader.dataRecieved.disconnect()

        # disconnect controls from functions
        self.channelComboBox.currentIndexChanged.disconnect()
        self.dataPointsNbrSpinBox.valueChanged.disconnect(self.DataPointsNbrChanged)
  
    def ChannelSelect(self):
        self.GetYScale()
        self.GetSweepsNbr()
        channel = self.channelComboBox.currentText()
        self.reader.selectChannel(channel)

    def DataPointsNbrChanged(self):
        PointsNbr = self.dataPointsNbrSpinBox.value()
        self.reader.SetDataPointsNbr(PointsNbr)
        
    def GetYScale(self):
        channel = self.channelComboBox.currentText()
        self.writeReader.emit("""VBS? 'return=app.Acquisition.""" + """C"""+channel[1] + """.VerScale' """)

    def SetYScale(self, value):
        channel = self.channelComboBox.currentText()
        scale = value/1000.0
        self.writeReader.emit("""VBS 'app.Acquisition.""" + """C"""+channel[1] + """.VerScale = """ + str(scale) + """'""")
        self.GetYScale()
        
    def GetCoupling(self):
        channel = self.channelComboBox.currentText()
        self.writeReader.emit("""VBS? 'return=app.Acquisition.""" + """C"""+channel[1] + """.Coupling' """)
 
    def GetSampleMode(self):
        string = """VBS? 'return=app.Acquisition.Horizontal.SampleMode'"""
        self.writeReader.emit(string)
        
    def SetSampleMode(self):
        mode = self.sampleModeComboBox.currentText()
        mode = '''"''' + mode + '''"'''
        string = """VBS 'app.Acquisition.Horizontal.SampleMode=""" + mode + """'"""
        self.writeReader.emit(string)

    def GetNbrOfSequence(self):
        string = """VBS? 'return=app.Acquisition.Horizontal.NumSegments'"""
        self.writeReader.emit(string)

    def GetTScale(self):
        string = """VBS? 'return=app.Acquisition.Horizontal.HorScale'"""
        self.writeReader.emit(string)

    def GetSweepsNbr(self):
        channel = self.channelComboBox.currentText()
        self.writeReader.emit("""VBS? 'return=app.Acquisition.""" + """C"""+channel[1] + """.AverageSweeps' """)
        
    def SetSweepsNbr(self, value):
        channel = self.channelComboBox.currentText()
        self.writeReader.emit("""VBS 'app.Acquisition.""" + """C"""+channel[1] + """.AverageSweeps=' """ + str(value))
        self.sweepsProgressBar.setMaximum(value)

    def GetTriggerMode(self):
        self.writeReader.emit("""VBS? 'return=app.Acquisition.TriggerMode' """)
 
    def GetTriggerSource(self):
        self.writeReader.emit("""VBS? 'return=app.Acquisition.Trigger.Edge.Source' """)

    def ClearSweeps(self):
        self.writeReader.emit("""VBS 'app.Acquisition.ClearSweeps' """)
    
    def TransmitData(self, data):
        if self.sweepsProgressBar.value() >= 1:
            self.emitData.emit(data)
            #print("emitData emitted")
        
    def quitScope(self):
        if self.scopeGroupBox.isChecked():
            self.scopeGroupBox.setChecked(False)
            #self.reader.Off()
        self.scope.Disconnect()


if __name__ == '__main__':
    
    class main(QtWidgets.QMainWindow):
        def __init__(self, parent=None):
            QtWidgets.QMainWindow.__init__(self, parent)
            self.scopeWidget = ScopeWidget()
            # create an empty widget used as a cenrtal widget for the qmainwindow and a container for other widgets :
            self.centralWidget = QtWidgets.QWidget()
            # creat the centrla widget :
            self.mainLayout = QtWidgets.QHBoxLayout()
            self.mainLayout.addWidget(self.scopeWidget)

            # create a Layout for the figure and the figure navigation
            self.figureLayout = QtWidgets.QVBoxLayout()
            # create the figure and the figure navigation
            self.figure = plt.Figure()
            
            self.axis = self.figure.add_subplot(111, facecolor='k')
#            self.axis.axis('auto')
            self.canvas = FigureCanvas(self.figure)             # Canvas Widget that displays the figure
            self.canvas.setMinimumWidth(700)
            self.canvas.setMinimumHeight(500)
            self.trace, = self.axis.plot([0,1],[0,0], color='yellow')
#            self.toolbar = NavigationToolbar(self.canvas, self) # Navigation widget
            # add the figure and the figure navigation to the figure layout
#            self.figureLayout.addWidget(self.toolbar)
            self.figureLayout.addWidget(self.canvas)
            # add the figure layout to the main layout
            self.mainLayout.addLayout(self.figureLayout)
            
            self.centralWidget.setLayout(self.mainLayout)
            self.setCentralWidget(self.centralWidget)

            self.setGeometry(100, 100, 680, 540)
#            self.setFixedSize(340, 270)
            self.setWindowTitle('Scope Control Widget')
            self.setWindowIcon(QIcon('web.png'))
            """
            main window creationand design
            """
            # setup menu bar
            self.statusBar()
            self.menuBar = self.menuBar()
            self.applicationMenu = self.menuBar.addMenu('Application')
            # create a start/stop action
            self.restartAction = QtWidgets.QAction('Restart', self)
            self.restartAction.setStatusTip('Reinitialize GPIB adresses')
            self.restartAction.triggered.connect(self.restartApplication)
            # create a quit action
            self.quitAction = QtWidgets.QAction('Quit', self)
            self.quitAction.setShortcut('Ctrl+Q')
            self.quitAction.setStatusTip('Exit application')
            self.quitAction.triggered.connect(self.close)
            # Add actions to the menubar
            self.applicationMenu.addAction(self.restartAction)
            self.applicationMenu.addAction(self.quitAction)

            self.scopeWidget.emitData.connect(self.Trace)
            self.scopeWidget.alertMessage.connect(self.statusBar().showMessage)

            self.show()
            
            
        def Trace(self, data):
            scale_y=self.scopeWidget.YScale
            scale_x=self.scopeWidget.XScale
            offset=self.scopeWidget.YOffset
          
            data_y=[]
            for i in range(len(data[1])):
                data_y.append(data[1][i]-offset)
            
            self.axis.set_xlim([-5*scale_x, 5*scale_x])
            self.axis.set_ylim([-4*scale_y, 4*scale_y])
            self.trace.set_xdata(data[0])
            self.trace.set_ydata(data_y)
            self.axis.grid(True)
            self.axis.set_ylabel("Tension (V)", fontsize=20)
            self.axis.set_xlabel("Time (s)", fontsize=20)
            self.canvas.draw()
            

        def restartApplication(self):   # keep this "restart" ???
            # stop application if necessary
            if self.scopeWidget.scopeGroupBox.isChecked():
                self.scopeWidget.scopeGroupBox.setChecked(False)
            self.scopeWidget.scopeGroupBox.setChecked(True)
                
        def closeEvent(self, event):
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                "Are you sure to quit?", QtWidgets.QMessageBox.Yes | 
                QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                self.scopeWidget.quitScope()
                event.accept()
                QtCore.QCoreApplication.instance().quit
            else:
                event.ignore()

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater) # seems to allow a proper handling of the "close" event under the anaconda distribution
    main = main()
    sys.exit(app.exec_())