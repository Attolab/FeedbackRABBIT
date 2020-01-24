# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 18:07:08 2020

@author: Commande
"""

from matplotlib import pyplot as plt
import numpy as np


data_nm = np.linspace(0,2000,100)


O1 = 2.757*10**(-3)
A1 = -5.886*10**(-4)
phi1 = 2.07896

O2 = 2.28497*10**(-3)
A2 = -5.0358*10**(-4)
phi2 = 8.26547*10**(-1)

omega_nm = 2.35*10**(15)/((3*10**17))

def SB_0noise(tau, O, A, phi): #SB without noise, tau in nm
    return O + A*np.cos(4*omega_nm*tau + phi) 

plt.plot(data_nm, SB_0noise(data_nm, O1, A1, phi1))
plt.plot(data_nm, SB_0noise(data_nm, O2, A2, phi2))
plt.plot(data_nm, np.arctan2())
plt.show()