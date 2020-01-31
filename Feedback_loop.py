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
    requestScopeBufferClear = QtCore.pyqtSignal()
    setScopeMode = QtCore.pyqtSignal(int)
    requestEmitDataReconnection = QtCore.pyqtSignal()
    def __init__(self, mode, tab1, tab2, tab3):   
        super(FeedbackLoop, self).__init__()
        
        
        self.mode = mode #feedback test or feedback
        self.tab1 = tab1
        self.tab2 = tab2
        self.tab3 = tab3
        
        self.startPos = float(self.tab3.locking_position_display.text())

        self.lockingPos = float(self.tab3.locking_position_display.text())
        currentPos = self.tab1.stageWidget.PositionNmLCD.intValue()
        
        self.moveTo = self.lockingPos - currentPos
        self.SB_vector_int = self.tab2.SB_vector_int
        self.BG_vector_int = self.tab2.BG_vector_int
        self.SBParam = self.tab3.SBParam   # SBParam = [O1, O2, A1, A2, phi1, phi2]
        self.a = self.tab2.a # slope of the error signal (rad/nm)
        self.b = self.tab2.b #rad
        self.maxError = float(self.tab3.max_error_display.text())
        self.tMax = self.tab3.tMax
        self.PIDParam = self.tab3.PIDParam  #PIDParam = [Kp, Ki, Kd, T]
        
  
        self.c_m_s = 3*10**8
        self.omega = 2.35*10**(15) 
        self.omega_nm = self.omega/(3*10**17) #pulsation in nm units
        self.feedbackNbr = self.tab3.feedbackNbr #label for this feedback loop, useful for stabilized scan
        
        self.data = []
        
        self.compensation_shift = 0. #how muched the stage has moved so far
        
        self.offsetDelay = 0.
        self.errorValue = self.tab3.errorValue
        self.command = 0.
        
        self.U = [0,0]
        self.E = [0,0,0]  #past error values
        
        self.mutex = QtCore.QMutex()
        self.smarActStopCondition = QtCore.QWaitCondition()

        # start the scanning loop
        self.run = True
        
        self.posDisplayed = False

    def Run(self):
        

        self.lockingPos = float(self.tab3.locking_position_display.text())         
        ############# first move to the intial position and wait until initial position is reached
        
        #print("begin Run")
        self.mutex.lock()
        #print("after mutex lock")
        self.requestFeedbackMotion.emit(self.moveTo)
        #print("after request motion")
        self.smarActStopCondition.wait(self.mutex)
        #print("after smaractstopcondition wait")
        self.mutex.unlock()
        #print("after initial unlock mutex")


        self.thread().msleep(1000)    
        delta_tau = 0.
        smarActPos = self.tab3.stageWidget.PositionNmLCD.value() 
        tau_t = self.lockingPos  #initial value of tau_t, at the begining of the feedback
        delay_drift = 0.
        print("initial tau_t = ", tau_t)
        
        self.lockingPos = float(self.tab3.locking_position_display.text())  #initial locking delay

        
        for ii in range(self.tMax):
            #print("")
            #print("RUN = ", self.run)
            
            if not self.run:
                #self.StoreData([])
                #print("not self.run")
                break    
            
            
            #print("")
            #print("feedback time = "+str(self.tab3.feedback_time))
            #print("")              
            #print("a = ", self.a)            
            ######## phase offset #########
 
            
            #print("lockingPos = ", self.lockingPos)
            

            
            tau_0 = self.lockingPos  #in nm
            
            #print(self.SBParam)
            
            V10 = self.SB_0noise(tau_0, self.SBParam[0], self.SBParam[2], self.SBParam[4])
            V20 = self.SB_0noise(tau_0, self.SBParam[1], self.SBParam[3], self.SBParam[5])
            
            #print("V10, V20 = ", V10, V20)     
            
            phi0 = self.Arctoperator(V10, V20, self.SBParam[0], self.SBParam[1], self.SBParam[2], self.SBParam[3])

            #print("phi0 = ", phi0)
            
        
            self.tab3.shapedErrorPlotDraw()        
         
            self.tab3.stepPercentSignal.emit(self.tab3.feedback_time)
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
                #print("waiting for data")
                self.thread().msleep(100)
                if not self.run:
                    break
             
            # 21-01-2020 : same as in scan loop, we removed the clear scope command
            #self.requestScopeMemoryClear.emit()               
          
            
            if self.mode == "Feedback": 
            
                ################### measure phase shift ##############
                # normalization ?????  need to normalize self.data[1] ?
                
                Background = np.trapz(self.data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])
                '''
                V1 = np.trapz(self.data[1][self.SB_vector_int[0]:self.SB_vector_int[1]])/(self.SB_vector_int[1]-self.SB_vector_int[0]) \
                - np.trapz(self.data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
                
                V2 = np.trapz(self.data[1][self.SB_vector_int[2]:self.SB_vector_int[3]])/(self.SB_vector_int[3]-self.SB_vector_int[2]) \
                - np.trapz(self.data[1][self.BG_vector_int[0]:self.BG_vector_int[1]])/(self.BG_vector_int[1]-self.BG_vector_int[0])
                '''
                
                
                #shaping of data (BG removed + normalization)
                
                retrieved_data = self.data[1] - Background
                norm = np.trapz(self.data[1])
                shaped_data = retrieved_data/norm
                
                V1 = np.trapz(shaped_data[self.SB_vector_int[0]:self.SB_vector_int[1]])/abs(self.SB_vector_int[1] - self.SB_vector_int[0])
                
                V2 = np.trapz(shaped_data[self.SB_vector_int[2]:self.SB_vector_int[3]])/abs(self.SB_vector_int[3] - self.SB_vector_int[2])
                
                # reconstruction of the phase
                
                phi_t = self.Arctoperator(V1, V2, self.SBParam[0], self.SBParam[1], self.SBParam[2], self.SBParam[3])            
                

                
                
            if self.mode == "Test Feedback":
               
                
                ################### generates artificial phase shift ##############                
                drift_speed = float(self.tab3.drift_speed_display.text())
                #drift_freq = float(self.tab3.drift_frequency_display.text())
                #drift_amp = float(self.tab3.drift_amp_display.text())                

                
                ###### HERE !!!! ##############  need to think about the compensation shift
                self.tab3.signal_noise = float(self.tab3.signal_noise_display.text())
                noise_level = self.tab3.signal_noise
                
                '''
                V1_t = self.tab3.SB_noisy(tau_t, self.tab2.O1, self.tab2.A1, self.tab2.phi1, noise_level)
                V2_t = self.tab3.SB_noisy(tau_t, self.tab2.O2, self.tab2.A2, self.tab2.phi2, noise_level)
                '''

                #print("rand = ",np.random.normal(1,noise_level))
                V1_t = np.random.normal(1,noise_level)*self.SB_0noise(tau_t, self.SBParam[0], self.SBParam[2], self.SBParam[4])
                V2_t = np.random.normal(1,noise_level)*self.SB_0noise(tau_t, self.SBParam[1], self.SBParam[3], self.SBParam[5])
                
                
                #print("V1_t, V2_t = ", V1_t, V2_t)                
                
                phi_t = self.Arctoperator(V1_t, V2_t, self.SBParam[0], self.SBParam[1], self.SBParam[2], self.SBParam[3])
            
                #print("phi_t = " +str(phi_t))                
                

            
            dphi_t = phi_t - phi0 
            
            #print("dphi_t = ", dphi_t)
            
            # taking the "saw teeths" into account
            
            dphi2_t = dphi_t
            
            if abs(dphi2_t) > np.pi:  #???
                print("tooth")
                if dphi2_t > 0 :
                    #print("if > 0")
                    dphi_t-=2*np.pi
                if dphi2_t < 0 :
                    dphi_t+=2*np.pi
            
            #print("dphi_t = ", dphi_t)
            delay_shift = dphi_t/self.a
            
            
              
            self.tab3.errorValue = -delay_shift
            #print("error value = "+str(self.tab3.errorValue))
            #self.thread().msleep(1000)
            
            
            ################## calculates command ###############  
            self.PIDParam = [self.tab3.Kp, self.tab3.Ki, self.tab3.Kd, self.tab3.T]   
            
            for i in range(2):
                self.E[i] = self.E[i+1]
            self.E[2] = self.tab3.errorValue
            
            self.U[0] = self.U[1]
        
            self.U[1] = self.PID(self.U[0], self.E, self.PIDParam[0], self.PIDParam[1], self.PIDParam[2], self.PIDParam[3])
            
            self.command = self.U[1]
            
            #print("command = ", self.command)

            ################# move ############################
            
            
            if abs(self.tab3.errorValue) < self.maxError:
                #print("move smaract")
                # freeze this loop while the stage is not at destination :
                #print('start motion')
                self.posDisplayed = False
                smarActPos = self.tab3.stageWidget.PositionNmLCD.value()
                self.mutex.lock()
                #print("mutex")
                if self.mode == "Feedback":
                    self.requestFeedbackMotion.emit(self.command/2)   # %2 because of the light goes back and forth in the delay line
                if self.mode == "Test Feedback":
                    self.requestFeedbackMotion.emit(self.command)  
                #print("after request move")
                self.smarActStopCondition.wait(self.mutex)
                #print("in mutex lock")
                self.mutex.unlock()
  
                '''
                self.thread().msleep(500)
                
                delta_tau = self.tab3.stageWidget.PositionNmLCD.value() - smarActPos
                
                tau_t += delta_tau 
                
                print("delta_tau = ", delta_tau)
                '''
                
            if self.tab3.linearDriftGroupBox.isChecked():
                tau_t -= drift_speed*1
                
                delay_drift += drift_speed*1
             
                self.tab3.drift_pos_display.display(delay_drift)
                

                
            '''
            while self.posDisplayed == False:
                #print("loop")
                self.thread().msleep(100)
                '''
            self.thread().msleep(100)    
            #delta_tau = self.tab3.stageWidget.PositionNmLCD.value() - smarActPos
                
            delta_tau = int(self.command)  #????
                
            tau_t += delta_tau 
                
            #print("delta_tau = ", delta_tau) 

              
                #self.compensation_shift += self.command
                #print("after mutex unlock")
            #print("position = "+str(self.tab3.stageWidget.PositionNmLCD.value())) 
            #self.requestEmitDataReconnection.emit()
            # trigger scope
            #self.setScopeMode.emit(0)

            ################ writes data in file  ###############
            #print("writes data")
            
            if self.run:       
            #write data in file
                self.folder = self.tab3.storedatafolder       
                
                index = str(ii)
                index = (4-len(index)) * "0" + index
                fileName = "Feedback" + str(self.feedbackNbr) + "File" + index + ".txt"
    
                pathFile = os.path.join(self.folder, fileName)
                file = open(pathFile,"w")
                
                file.write("Feedback time = "+str(ii)+"\n")
                file.write("Locking delay (nm) = "+str(tau_0)+"\n")               
                file.write("Current pump-probe delay (nm) = "+str(tau_t)+"\n")                
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
            self.thread().msleep(100)   
            self.tab3.feedbackStepFinished.emit() 
            
        self.feedbackFinished.emit()
        self.tab3.feedback_time = 0
        
        # 21-01-2020

        
        print("LOOP OUT")
    def StoreData(self, data):
        self.data = data
        if data != []:
            # stop the scope while the main loop write the data in a file
            self.setScopeMode.emit(3)

        
    def Stop(self):
        self.run = False
        print("run set to FALSE")
        
        
        

    def newPosSmarAct(self):
        self.posDisplayed = True

    def Arctoperator(self, V1, V2, O1, O2, A1, A2):
        return np.arctan2((V1-O1)/A1, (V2-O2)/A2)        
        
    def PID(self, U, E, Kp, Ki, Kd, T):
        return U + Kp*(E[2]-E[1]) + T*Ki*E[2] + (Kd/T)*(E[2]-2*E[1]+E[0])
    
    def SB_0noise(self, tau, O, A, phi): #SB without noise, tau in nm

        return O + A*np.cos(4*self.omega_nm*tau + phi)    
    
    def SB_noisy(self, tau, O, A, phi, noise): #SB with noise, tau in nm
        return np.random.normal(1, noise)*(O + A*np.cos(4*self.omega_nm*tau + phi))

    