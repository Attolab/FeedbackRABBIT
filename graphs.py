# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 18:07:08 2020

@author: Commande
"""

from matplotlib import pyplot as plt
import numpy as np


data_nm = np.linspace(0,2000,10000)


O1 = 2.88*10**(-3)
A1 = -7.11*10**(-4)
phi1 = 2.095

O2 = 2.6*10**(-3)
A2 = -5.8*10**(-4)
phi2 = 7.95*10**(-1)

omega_nm = 2.35*10**(15)/((3*10**17))

def SB_0noise(tau, O, A, phi): #SB without noise, tau in nm
    return O + A*np.cos(4*omega_nm*tau + phi) 

SB1 = SB_0noise(data_nm, O1, A1, phi1)
SB2 = SB_0noise(data_nm, O2, A2, phi2)
#plt.plot(data_nm, SB_0noise(data_nm, O1, A1, phi1))
#plt.plot(data_nm, SB_0noise(data_nm, O2, A2, phi2))
plt.plot(data_nm, np.arctan2((SB1 - O1)/A1, (SB2 - O2)/A2))
plt.grid(True)
plt.show()