"""
Class for the SmarAct transation stage control
if main: this python script includes the widget in a window and adds a menu to it


Hold ON procedure made automatic, the system is always in closed-loop
"""
import sys
import ctypes

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QIcon

import time

# TODO :
# 0) spinbox signals : return pressed??
# 1) change the thread closing method to deleteLater ???
# 2) handle collisions
# 2)a) create variables holding the endpoints?
# 2)b) cap motion or forbid it?

"""
Smaract dll declaration followed by the functions prototyping
doc at : C:\SmarAct\MCS\Documentation
MCS Programmers Guide.pdf is very complete
"""

SmaractDll = ctypes.CDLL ("C:\\SmarAct\\MCS\\SDK\\lib64\\MCSControl.dll")

# prototype of the SA_FindSystems function
# uint32_t SA_FindSystems(const CStr options, CStr outList, uint32_t *ioListSize);
SmaractDll.SA_FindSystems.argtypes = [
    ctypes.POINTER(ctypes.c_char),# Parameter 1
    ctypes.c_char_p,# Parameter 2
    ctypes.POINTER(ctypes.c_ulong)]# Parameter 3
SmaractDll.SA_FindSystems.restype = ctypes.c_ulong

# prototype of the SA_OpenSystem function
# uint32_t SA_OpenSystem(uint32_t *systemIndexOut, const CStr systemLocator, const CStr options);
SmaractDll.SA_OpenSystem.argtypes = [
    ctypes.POINTER(ctypes.c_ulong),# Parameter 1 : systemIndexOut
    ctypes.c_char_p,# Parameter 2 : systemLocator
    ctypes.c_char_p]# Parameter 3 : options
SmaractDll.SA_OpenSystem.restype = ctypes.c_ulong

# prototype of the SA_GetNumberOfChannels function
# uint32_t SA_GetNumberOfChannels(uint32_t systemIndex, uint32_t *channels);
SmaractDll.SA_GetNumberOfChannels.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.POINTER(ctypes.c_ulong)]# Parameter 2 : pointer to the number of channels
SmaractDll.SA_GetNumberOfChannels.restype = ctypes.c_ulong

# prototype of the SA_GetChannelType function
# uint32_t SA_GetChannelType(uint32_t systemIndex, uint32_t channelIndex, uint32_t *type);
SmaractDll.SA_GetChannelType.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : pointer to the number of channels
    ctypes.POINTER(ctypes.c_ulong)]# Parameter 3 : pointer to the type of channel
SmaractDll.SA_GetChannelType.restype = ctypes.c_ulong

# prototype of the SA_SetSensorEnabled_A function
# uint32_t SA_SetSensorEnabled_A(uint32_t systemIndex, uint32_t enabled);
SmaractDll.SA_SetSensorEnabled_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong]# Parameter 2 : enabled (meaning "sensorEnabled")
SmaractDll.SA_SetSensorEnabled_A.restype = ctypes.c_ulong
# sensorEnabled :
# 0 = SA_SENSOR_DISABLED
# 1 = SA_SENSOR_ENABLED
# 2 = SA_SENSOR_POWERSAVE

# prototype of the SA_SetSensorType_A function
# uint32_t SA_SetSensorType_A(uint32_t systemIndex, uint32_t channelIndex, uint32_t type);
SmaractDll.SA_SetSensorType_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : channelIndex
    ctypes.c_ulong]# Parameter 3 : sensorType
SmaractDll.SA_SetSensorType_A.restype = ctypes.c_ulong

# prototype of the SA_SetClosedLoopMoveSpeed_A function
# uint32_t SA_SetClosedLoopMoveSpeed_A(uint32_t systemIndex, uint32_t channelIndex, uint32_t speed);
SmaractDll.SA_SetClosedLoopMoveSpeed_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : channelIndex
    ctypes.c_ulong]# Parameter 3 : speed
SmaractDll.SA_SetClosedLoopMoveSpeed_A.restype = ctypes.c_ulong

# prototype of the SA_GetClosedLoopMoveSpeed_A function
# uint32_t SA_GetClosedLoopMoveSpeed_A(uint32_t systemIndex, uint32_t channelIndex);
SmaractDll.SA_GetClosedLoopMoveSpeed_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong]# Parameter 2 : channelIndex
SmaractDll.SA_GetClosedLoopMoveSpeed_A.restype = ctypes.c_ulong

# prototype of the SA_SetReportOnComplete_A function
# uint32_t SA_SetReportOnComplete_A(uint32_t systemIndex, uint32_t channelIndex, uint32_t report);
SmaractDll.SA_SetReportOnComplete_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : channelIndex
    ctypes.c_ulong]# Parameter 3 : report
SmaractDll.SA_SetReportOnComplete_A.restype = ctypes.c_ulong
# report :
# 0 : SA_NO_REPORT_On_COMPLETE
# 1 : SA_REPORT_On_COMPLETE

# prototype of the SA_CalibrateSensor_A function
# uint32_t SA_CalibrateSensor_A(uint32_t systemIndex, uint32_t channelIndex);

SmaractDll.SA_CalibrateSensor_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong]# Parameter 2 : channelIndex
SmaractDll.SA_CalibrateSensor_A.restype = ctypes.c_ulong

# prototype of the SA_FindReferenceMark_A function
# uint32_t SA_FindReferenceMark_A(uint32_t systemIndex, uint32_t channelIndex, uint32_t direction, uint32_t holdTime, uint32_t autoZero);
SmaractDll.SA_FindReferenceMark_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : channelIndex
    ctypes.c_ulong,# Parameter 3 : direction
    ctypes.c_ulong,# Parameter 4 : holdTime
    ctypes.c_ulong]# Parameter 5 : autoZero
SmaractDll.SA_FindReferenceMark_A.restype = ctypes.c_ulong

# prototype of the SA_GotoPositionAbsolute_A function
# uint32_t SA_GotoPositionAbsolute_A(uint32_t systemIndex, uint32_t channelIndex, int32_t position, uint32_t holdTime);
SmaractDll.SA_GotoPositionAbsolute_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : channelIndex
    ctypes.c_long,# Parameter 3 : position
    ctypes.c_ulong]# Parameter 4 : holdTime
SmaractDll.SA_GotoPositionAbsolute_A.restype = ctypes.c_ulong

# prototype of the SA_GetPosition_A function
# uint32_t SA_GetPosition_A(uint32_t systemIndex, uint32_t channelIndex);
SmaractDll.SA_GetPosition_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong]# Parameter 2 : channelIndex
SmaractDll.SA_GetPosition_A.restype = ctypes.c_ulong

# prototype of the SA_CloseSystem function
# uint32_t SA_CloseSystem(uint32_t systemIndex);
SmaractDll.SA_CloseSystem.argtypes = [
    ctypes.c_ulong]# Parameter 1 : systemIndex
SmaractDll.SA_CloseSystem.restype = ctypes.c_ulong

# class prototyping Data Packets Structure
class DataPacketStructure(ctypes.Structure):
    # creates a struct to work with the data packets used in the asynchronous mode
    _fields_ = [('packetType', ctypes.c_ulong), # type of packet
                ('channelIndex', ctypes.c_ulong), # source channel
                ('data1', ctypes.c_ulong), # data field
                ('data2', ctypes.c_long), # data field
                ('data3', ctypes.c_long), # data field
                ('data4', ctypes.c_ulong)] # data field

# prototype of the SA_CloseSystem function
# uint32_t SA_ReceiveNextPacket_A(uint32_t systemIndex, uint32_t timeout, void *packet);
SmaractDll.SA_ReceiveNextPacket_A.argtypes = [
    ctypes.c_ulong,# Parameter 1 : systemIndex
    ctypes.c_ulong,# Parameter 2 : timeout
    ctypes.POINTER(DataPacketStructure)]# Parameter 3 : data packet pointer
SmaractDll.SA_ReceiveNextPacket_A.restype = ctypes.c_ulong



"""
class handling the SmarAct reading operations
"""
class SmarActReader(QtCore.QObject):
    newPosition = QtCore.pyqtSignal(int)
    motionEnded = QtCore.pyqtSignal()
    def __init__(self, holdingWidget):
        super(SmarActReader, self).__init__()
        self.holdingWidget = holdingWidget
        self.systemIndex = holdingWidget.systemIndex
        self.channelIndex = self.holdingWidget.ChannelComboBox.currentIndex() - 1
        # get rid of the "holdingWidget but store :
        # 1) system Index
        # 2) self.holdingWidget.ChannelComboBox.currentIndex() - 1
        # and emit signals or :
        # 1) PositionNmLCD
        # 2) ???
        self.isRunning = False
        self.struct = DataPacketStructure(1,1,1,1,1,1)

    def run(self):
        self.isRunning = True
        # initialize packet reading parameters
        status = 9
        timeout = 500
        self.struct = DataPacketStructure(1,1,1,1,1,1)
        # reading loop : the SmarAct controler sends information by packets
        while self.isRunning:
            # 1) read packet
            status = SmaractDll.SA_ReceiveNextPacket_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(timeout), ctypes.byref(self.struct))
            # 2) analyse packet
            if self.struct.packetType == 0:
                SmaractDll.SA_GetPosition_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(self.channelIndex))
            elif self.struct.packetType == 2:
#                print "Channel " + str(struct.channelIndex) + " is at position : " + str(struct.data2) + " nm"
                self.newPosition.emit(self.struct.data2)
                #print(self.struct.data2)
            elif self.struct.packetType == 3:
                self.motionEnded.emit()
                print("emit motionEnded")
            elif self.struct.packetType == 12:
                print("Channel " + str(self.struct.channelIndex) + "'s speed has been set to " + str(self.struct.data1) + " nm/s")
            # pause loop
            self.thread().msleep(100)
        # 
        self.thread().exit()

    def stop(self):
        self.isRunning = False



"""
class handling the Stage widget
"""
qtCreatorFile = "SmarActUI_f.ui"
Ui_StageWidget, QtBaseClass = loadUiType(qtCreatorFile)
class StageWidget(QtWidgets.QFrame, Ui_StageWidget):
    def __init__(self, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setupUi(self)          #self.frame = uic.loadUi("StagePyQt4UI.ui")
        self.systemIndex = 0
        
        self.POS = 0.

        self.ControlerComboBox.currentIndexChanged.connect(self.onControlerSelect)
        # speed spinbox keybordtracking set off by default
        self.SpeedSpinBox.valueChanged.connect(self.setSpeed)
        # hold position pushbutton connection
        """
        self.setHoldPushButton.toggled.connect(self.HoldPositionOnOff)
        """
        # position spinbox keybordtracking set off by default
        self.PositionNmSpinBox.valueChanged.connect(self.GotoPositionAbsolute)
        self.StepLeftPushButton.clicked.connect(lambda x : self.PositionNmSpinBox.setValue(self.PositionNmSpinBox.value() - self.StepSpinBox.value()))
        self.StepRightPushButton.clicked.connect(lambda x : self.PositionNmSpinBox.setValue(self.PositionNmSpinBox.value() + self.StepSpinBox.value()))
        
        self.StepLeftPushButton.clicked.connect(lambda x : self.PositionFsSpinBox.setValue(self.PositionFsSpinBox.value() - self.StepSpinBox.value()/300.))
        self.StepRightPushButton.clicked.connect(lambda x : self.PositionFsSpinBox.setValue(self.PositionFsSpinBox.value() + self.StepSpinBox.value()/300.))
        self.FindRefPushButton.clicked.connect(self.FindReference)
        self.CalibrationPushButton.clicked.connect(self.Calibration)   

        self.FindSystems()
        self.ChannelComboBox.currentIndexChanged.connect(self.onChannelSelect)


    def FindSystems(self):
        # disconnect the controler combobox while we're working on it
        self.ControlerComboBox.currentIndexChanged.disconnect()
#        use ctypes.create_unicode_buffer( )
        ioListSize = 4096
        options = ctypes.c_char()
        outList = (' ' * ioListSize).encode('ascii')
        ioListSize = ctypes.c_ulong(ioListSize)
        status = SmaractDll.SA_FindSystems(ctypes.byref(options), outList, ctypes.byref(ioListSize))
        # handle errors (= non-zero status values) !!!
        outList = outList.decode('utf-8').split('\n')
        self.ControlerComboBox.clear()
        self.ChannelComboBox.clear()
        self.ControlerComboBox.addItems([''] + outList)

        # reconnect the controler combobox
        self.ControlerComboBox.currentIndexChanged.connect(self.onControlerSelect)
#        if len(outList) >= 2:
#            self.ControlerComboBox.setCurrentIndex(1)
        return status
    

    def onControlerSelect(self, index):
        if index == 0:
            # disable controls and then close the current controler
            self.ChannelComboBox.setEnabled(False)
            self.releaseControler()
            # remove the non-empty entries of the channelComboBox
            for ii in range(self.ChannelComboBox.count(),0,-1):
                self.ChannelComboBox.removeItem(ii)
        else:
            # take control of the selected controler
            locator = str(self.ControlerComboBox.currentText())
            systemIndex = ctypes.c_ulong(0)
#            options = ctypes.c_char_p('async, reset') # reset??? keep position???
            options = 'async'.encode('ascii') # reset??? keep position???
            status = SmaractDll.SA_OpenSystem(ctypes.byref(systemIndex), locator.encode('ascii'), options)
            # handle errors (= non-zero status values) !!!
            if status == 0:
                self.systemIndex = systemIndex.value
            
            # read the available channels and create corresponding entries in the channels combobox
            numberOfChannels = ctypes.c_ulong(0)
            status = SmaractDll.SA_GetNumberOfChannels(ctypes.c_ulong(self.systemIndex), ctypes.byref(numberOfChannels))
            if status == 0:
                # block the ChannelComboBox signals while it is manipulated
                self.ChannelComboBox.blockSignals(True)
                # set the Channel comboBox items according to the motors available on the selected controler
                self.ChannelComboBox.clear()
                self.ChannelComboBox.addItems([' '])
                positioner = 1
                endEffector = 1
                # loop over the detected motors and add an entry for each in the ChannelsComboBox
                for ii in range(numberOfChannels.value):
                    channelIndex = ctypes.c_ulong(ii)
                    channelType = ctypes.c_ulong(2)
                    # channel type can be motor or endEffector
                    # the following conditional statement sorts them
                    status = SmaractDll.SA_GetChannelType(ctypes.c_ulong(self.systemIndex), channelIndex, ctypes.byref(channelType))
                    if channelType.value == 0:
                        self.ChannelComboBox.addItems(["positioner " + str(positioner)])
                        positioner += 1
                    elif channelType.value == 1:
                        self.ChannelComboBox.addItems(["end effector " + str(endEffector)])
                        endEffector += 1
                self.ChannelComboBox.setEnabled(True)
                # unblock the ChannelComboBox signals
                self.ChannelComboBox.blockSignals(False)
            
            # enable sensors 
            sensorEnabled = 1
            status = SmaractDll.SA_SetSensorEnabled_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(sensorEnabled))
            
    def onChannelSelect(self, index):
        # stop the SmarAct reading thread if running
        if hasattr(self, 'smarActReaderThread'):
            self.smarActReader.newPosition.disconnect()
            self.smarActReader.stop()
            # wait for the thread to stop before going on
            while self.smarActReader.thread().isRunning():
                self.thread().msleep(100)
            # need terminate after isRunning turned to False ???
            self.smarActReaderThread.terminate()
            # delete the thread from the from the instance :
            # avoid entering this if statement the next time the channel combobox will be toggled
            del self.smarActReaderThread
            
            
        # handle a switching of the combobox to 0
        if index == 0:
            # enable the Controler selection ComboBox and disable the groupbox
            self.ControlerComboBox.setEnabled(True)
            self.StageGroupBox.setTitle('OFF')
            # set groupbox displays to off state
            self.StageGroupBox.setEnabled(False)

            return 0
        else:
            # set the sensor type corresponding to the channel: 1 -> SA_S_SENSOR_TYPE
            sensorType = 1
            channelIndex = index - 1
            status = SmaractDll.SA_SetSensorType_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(channelIndex), ctypes.c_ulong(sensorType))

            # set speed
            self.setSpeed(self.SpeedSpinBox.value())
        
            # set report on complete state
            report = 1
            status = SmaractDll.SA_SetReportOnComplete_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(channelIndex), ctypes.c_ulong(report))

            # start the SmarAct reading thread
            self.smarActReaderThread = QtCore.QThread()
            self.smarActReader = SmarActReader(self)
            self.smarActReader.moveToThread(self.smarActReaderThread)
            self.smarActReaderThread.started.connect(self.smarActReader.run)
            self.smarActReader.newPosition.connect(self.displayNewPosition)  # listen to new position values
            self.smarActReaderThread.start()

            # disable the Controler selection ComboBox and enable the groupbox
            self.StageGroupBox.setEnabled(True)
            self.ControlerComboBox.setEnabled(False)
            self.StageGroupBox.setTitle('ON')
            return status
    
    def Calibration(self):
        channelIndex = self.ChannelComboBox.currentIndex() - 1
        status = SmaractDll.SA_CalibrateSensor_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(channelIndex))
        return status
    '''    
    def FindReference(self):
        channelIndex = self.ChannelComboBox.currentIndex() - 1
        direction = 0   # SA_FORWARD_DIRECTION
        if self.setHoldPushButton.isChecked():
            holdTime = 60000
        else:
            holdTime = 0
            
        autoZero = 1
        status = SmaractDll.SA_FindReferenceMark_A(ctypes.c_ulong(self.systemIndex), 
                                                    ctypes.c_ulong(channelIndex),
                                                    ctypes.c_ulong(direction),
                                                    ctypes.c_ulong(holdTime),
                                                    ctypes.c_ulong(autoZero))
        
        self.PositionNmSpinBox.setValue(0)   #the new position is 0 after FindReference
        self.PositionFsSpinBox.setValue(0)
        return status
        '''  
    def FindReference(self):
        channelIndex = self.ChannelComboBox.currentIndex() - 1
        direction = 0   # SA_FORWARD_DIRECTION
        
        holdTime = 60000
        #holdTime = 200
        autoZero = 1
        status = SmaractDll.SA_FindReferenceMark_A(ctypes.c_ulong(self.systemIndex), 
                                                    ctypes.c_ulong(channelIndex),
                                                    ctypes.c_ulong(direction),
                                                    ctypes.c_ulong(holdTime),
                                                    ctypes.c_ulong(autoZero))
        
        self.PositionNmSpinBox.setValue(0)   #the new position is 0 after FindReference
        self.PositionFsSpinBox.setValue(0)
        return status

    def setSpeed(self, speed):
        channelIndex = self.ChannelComboBox.currentIndex() - 1
        status = SmaractDll.SA_SetClosedLoopMoveSpeed_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(channelIndex), ctypes.c_ulong(speed))

        status = SmaractDll.SA_GetClosedLoopMoveSpeed_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(channelIndex))
        return status
    
    def GotoPositionAbsolute(self, position):
     
        #get the position during feedback
        SmaractDll.SA_GetPosition_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(self.smarActReader.channelIndex))
        self.smarActReader.newPosition.emit(self.smarActReader.struct.data2)
        
        self.PositionFsSpinBox.setValue(position/300.)
        channelIndex = self.ChannelComboBox.currentIndex() - 1
        #holdTime = 200
        holdTime = 60000   
        status = SmaractDll.SA_GotoPositionAbsolute_A(ctypes.c_ulong(self.systemIndex), ctypes.c_ulong(channelIndex), ctypes.c_long(position), ctypes.c_ulong(holdTime))
        
        

    
        return status
    """ 
    def HoldPositionOnOff(self):
        if self.setHoldPushButton.isChecked():
            self.setHoldPushButton.setText('Hold ON')
        else:
            self.setHoldPushButton.setText('Hold OFF')
       """
    """   
    def HoldPositionOnOff(self):
        self.setHoldPushButton.setText('Automatic stabilization')
        """
            
    def releaseControler(self):
        status = SmaractDll.SA_CloseSystem(ctypes.c_ulong(self.systemIndex))
        return status
    
    def displayNewPosition(self, pos):
        self.PositionNmLCD.display(pos)
        self.PositionProgressBar.setValue(pos)
        #print("smaract pos = "+str(pos))
        #self.POS = pos



if __name__ == '__main__':
    
    class SmarActWindow(QtWidgets.QMainWindow):
        def __init__(self, parent=None):
            QtWidgets.QMainWindow.__init__(self, parent)
            self.StageWidget = StageWidget()
            self.setCentralWidget(self.StageWidget)
            self.setGeometry(100, 100, 340, 270)
            self.setFixedSize(340, 270)
            self.setWindowTitle('Stage Control Widget (Automatic Closed-loop')
            self.setWindowIcon(QIcon('web.png'))
            """
            main window creationand design
            """
            # setup menu bar
            self.statusBar()
            self.menuBar = self.menuBar()
            self.applicationMenu = self.menuBar.addMenu('Application')
            # create a quit action
            self.quitAction = QtWidgets.QAction('Quit', self)
            self.quitAction.setShortcut('Ctrl+Q')
            self.quitAction.setStatusTip('Exit application')
            self.quitAction.triggered.connect(self.close)
            # Add actions to the menubar
            self.applicationMenu.addAction(self.quitAction)

        def closeEvent(self, event):
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                "Are you sure to quit?", QtWidgets.QMessageBox.Yes | 
                QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                #self.StageWidget.StageGroupBox.setChecked(False)
                #self.StageWidget.ControlerComboBox.setCurrentIndex(0)
                if self.StageWidget.ChannelComboBox.currentIndex() != 0:
                    self.StageWidget.ChannelComboBox.setCurrentIndex(0)
                if self.StageWidget.ControlerComboBox.currentIndex() != 0:
                    self.StageWidget.ControlerComboBox.setCurrentIndex(0)
                event.accept()
#                QtCore.QCoreApplication.instance().quit
            else:
                event.ignore()         

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater) # seems to allow a proper handling of the "close" event under the anaconda distribution
    smarActWindow = SmarActWindow()
    smarActWindow.show()
    sys.exit(app.exec_())
