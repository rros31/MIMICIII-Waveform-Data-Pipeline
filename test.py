# -*- coding: utf-8 -*-
"""
Created on Tue May 24 10:28:12 2022

@author: cca78
"""

import HRV
import time

start = time.time()
HRV.run_hrv_analysis()
stop = time.time()
print(stop - start)