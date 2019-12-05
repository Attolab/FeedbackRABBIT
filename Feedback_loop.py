# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 11:44:48 2019

@author: mluttmann
"""


import os

import PyQt5.QtCore as QtCore

import datetime
import numpy as np



# TODO :
# 1) the scanning loop does NOT stop when quitting the application !!!!!
# 2) add a moveAbolute signal to the ScanningLoop to send the smarAct to the start position ???

"""
class handling the feedback operations
"""
class FeedbackLoop(QtCore.QObject):
    feedbackFinished = QtCore.pyqtSignal()
    requestFeedbackMotion = QtCore.pyqtSignal(int)
    requestScopeMemoryClear = QtCore.pyqtSignal()
    setScopeMode = QtCore.pyqtSignal(int)
    requestEmitDataReconnection = QtCore.pyqtSignal()
    def __init__(self, mode, tab3, currentPos, lockingPos, SB_vector_int, BG_vector_int, SBParam, a, maxError, PIDParam, folder, tMax, feedbackNbr, errorValue):   #PIDParam = [Kp, Ki, Kd, T]
        super(FeedbackLoop, self).__init__()
        
        
        self.mode = mode #feedback test or feedback
        self.tab3 = tab3

        self.lockingPos = lockingPos
        
        self.moveTo = self.lockingPos - currentPos
        self.SB_vector_int = SB_vector_int
        self.BG_vector_int = BG_vector_int
        self.SBParam = SBParam   # SBParam = [O1, O2, A1, A2, phi1, phi2]
        self.a = a # slope of the error signal (rad/nm)
        self.maxError = maxError
        self.tMax = tMax
        self.PIDParam = PIDParam
        self.folder = folder
  
        self.c_m_s = 3*10**8
        self.omega = 2.35*10**(15)        
        self.feedbackNbr = feedbackNbr #label for this feedback loop, useful for stabilized scan
        
        self.data = []
        
        self.offsetDelay = 0.
        self.errorValue = errorValue
        self.command = 0.
        
        self.U = [0,0]
        self.E = [0,0,0]  #past error values
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()

        # start the scanning loop
        self.run = True

    def Run(self):
        
        
        
        ############# first move to the intial position and wait until initial position is reached
        
        print("begin Run")
        self.mutex.lock()
        print("after mutex lock")
        self.requestFeedbackMotion.emit(self.moveTo)
        #print("after request motion")
        self.smarActStopCondition.wait(self.mutex)
        #print("after smaractstopcondition wait")
        self.mutex.unlock()
        print("after initial unlock mutex")
        
        ######## measure delay offset #########
        
        tau_s = self.lockingPos*10**(-9)/self.c_m_s
        
        V10 = self.SB_0noise(tau_s, self.SBParam[0], self.SBParam[2], self.SBParam[4])
        V20 = self.SB_0noise(tau_s, self.SBParam[1], self.SBParam[3], self.SBParam[5])
        
        Dphi0 = self.Arctoperator(V10, V20, self.SBParam[0], self.SBParam[1], self.SBParam[2], self.SBParam[3])
        
        self.offsetDelay = Dphi0/self.a        
        
        
        
        
        for ii in range(self.tMax):
            print("")
            print("RUN = ", self.run)
            
            if not self.run:
                self.StoreData([])
                print("not self.run")
                break
            
            print("feedback time = "+str(self.tab3.feedback_time))
            
            #print("mode = " +str(self.mode))
#            # clear scope memory
#            print('clear memory')

            
            #print("beginning of step")
            #################### take scope data ################
            
            # allow data emition fro mthe scopeWidget
            self.requestEmitDataReconnection.emit()
            # trigger scope
            self.setScopeMode.emit(0)           
            # read scope 
            
            while self.data == []:
                #print("waiting 1")
                self.thread().msleep(100)
                if not self.run:
                    break
                
            self.requestScopeMemoryClear.emit()               

            
            if self.mode == "Feedback": 
            
                ################### measure phase shift ##############
            
                V1 = np.trapz(self.data[1][self.SB_vector_int[0]:self.SB_vector_int[1]])/(self.SB_vector_int[1]-self.SB_vector_int[0]) \
                - np.trapz(self.data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
                
                V2 = np.trapz(self.data[1][self.SB_vector_int[2]:self.SB_vector_int[3]])/(self.SB_vector_int[3]-self.SB_vector_int[2]) \
                - np.trapz(self.data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
                           
                Dphi = self.Arctoperator(V1, V2, self.SBParam[0], self.SBParam[1], self.SBParam[2], self.SBParam[3])            
            
                ################## calculates command ###############
                
                
            if self.mode == "Test Feedback":
               
                
                ################### generates artificial phase shift ##############                
                drift_speed = float(self.tab3.drift_speed_display.text())
                drift_freq = float(self.tab3.drift_frequency_display.text())
                drift_amp = float(self.tab3.drift_amp_display.text())                
                
                smarActPos = self.tab3.stageWidget.PositionNmLCD.value()
                tau_s = smarActPos*10**(-9)/self.tab3.tab2.c_m_s               
                
                compensation_shift = smarActPos - self.lockingPos #how much we've moved so far 

                if self.tab3.linearDriftGroupBox.isChecked():
                    current_tau_nm = self.tab3.lindrift(ii, self.lockingPos, drift_speed) 
                
                
                if self.tab3.oscillDriftGroupBox.isChecked():
                    current_tau_nm = self.tab3.oscilldrift(ii, self.lockingPos, drift_freq, drift_amp)
                    
                self.tab3.drift_pos_display.display(current_tau_nm - self.lockingPos)
                    
                current_tau_nm_compensated = current_tau_nm - compensation_shift # this is the relevant delay to be used in the test signals
                current_tau_s_compensated = current_tau_nm_compensated*10**(-9)/self.tab3.tab2.c_m_s  # delay in seconds


                self.tab3.signal_noise = float(self.tab3.signal_noise_display.text())
                
                #with compensation due to feedback
                V1 = self.tab3.SB_noisy(current_tau_s_compensated, self.tab3.tab2.O1, self.tab3.tab2.A1, self.tab3.tab2.phi1, self.tab3.signal_noise)
                V2 = self.tab3.SB_noisy(current_tau_s_compensated, self.tab3.tab2.O2, self.tab3.tab2.A2, self.tab3.tab2.phi2, self.tab3.signal_noise)

                Dphi = self.Arctoperator(V1, V2, self.SBParam[0], self.SBParam[1], self.SBParam[2], self.SBParam[3])
                
                #print("Dphi calculated with test signals = " +str(Dphi))
                
            self.tab3.errorValue = Dphi/self.a - self.offsetDelay
            print("error value = "+str(self.errorValue))
            #self.thread().msleep(1000)
            
            for i in range(2):
                self.E[i] = self.E[i+1]
            self.E[2] = self.tab3.errorValue
            
            self.U[0] = self.U[1]
        
            self.U[1] = self.PID(self.U[0], self.E, self.PIDParam[0], self.PIDParam[1], self.PIDParam[2], self.PIDParam[3])
            
            self.command = self.U[1]
            
            print("command = "+str(self.command))
            #self.command = self.errorValue*self.PIDParam[0]
            #print("command = "+str(self.command))
            if int(self.command) == 0:
                self.command = int(self.command) + 1
                #print("new command = "+str(self.command))
            
            ################# move ############################
            
            
            if self.tab3.errorValue < self.maxError:
                # freeze this loop while the stage is not at destination :
                #print('start motion')
                self.mutex.lock()
                #print("mutex")
                self.requestFeedbackMotion.emit(self.command)
                #print("after request move")
                self.smarActStopCondition.wait(self.mutex)
                #print("after .wait in feedback")
                self.mutex.unlock()
                #print("after mutex unlock")
            #print("position = "+str(self.tab3.stageWidget.PositionNmLCD.value())) 
            #self.requestEmitDataReconnection.emit()
            # trigger scope
            #self.setScopeMode.emit(0)

            ################ writes data in file  ###############
            #print("writes data")
            
        
            #write data to file
            
            index = str(ii)
            index = (4-len(index)) * "0" + index
            fileName = "Feedback" + str(self.feedbackNbr) + "File" + index + ".txt"

            pathFile = os.path.join(self.folder, fileName)
            file = open(pathFile,"w")
            
            file.write("Feedback time = "+str(ii)+"\n")
            file.write("Stage position (nm) = "+str(smarActPos)+"\n")
            file.write("Error value (nm) = "+str(self.tab3.errorValue)+"\n")
            file.write("Kp, Ki, Kd = "+str(self.PIDParam[0])+", "+str(self.PIDParam[1])+", "+str(self.PIDParam[2])+"\n")
            x = datetime.datetime.now()
            file.write("Date and time = "+str(x)+"\n")            
            
            for pp in range(len(self.data[0])):
                file.write('%f\t%f\n' % (self.data[0][pp], self.data[1][pp]))
            file.close()
            self.StoreData([])
            #print("after write data")
            
            self.tab3.feedback_time += 1
            
        self.feedbackFinished.emit()
        self.tab3.feedback_time = 0
        print("LOOP OUT")
    def StoreData(self, data):
        self.data = data
        if data != []:
            # stop the scope while the main loop write the data in a file
            self.setScopeMode.emit(3)

        
    def Stop(self):
        self.run = False
        print("run set to FALSE")
        
        


    def Arctoperator(self, V1, V2, O1, O2, A1, A2):
        return np.arctan(((V1-O1)*A2)/((V2-O2)*A1))        
        
    def PID(self, U, E, Kp, Ki, Kd, T):
        return U + Kp*(E[2]-E[1]) + T*Ki*E[2] + (Kd/T)*(E[2]-2*E[1]+E[0])
    
    def SB_0noise(self, tau, O, A, phi): #SB without noisy, tau in seconds
        return O + A*np.cos(4*self.omega*tau + phi)    
    


    