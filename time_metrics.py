# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 13:15:48 2022

@author: cca78
"""
import numpy as np
import os
import matplotlib.pyplot as plt


def rmssd(intervals):
    sd = np.diff(intervals)
    rmssd = np.sqrt(np.mean(sd**2))
    return rmssd

def sdnn(intervals):
    sdnn = np.std(intervals)
    return sdnn

def pnn50(intervals):
    sd = np.diff(intervals)
    n = np.count_nonzero(sd > 0.05)
    pnn50 = n / len(sd)
    return pnn50

def time_analysis(intervals):

    return {"rmssd":rmssd(intervals),
            "sdnn":sdnn(intervals),
            "pnn50":pnn50(intervals)}


# #test code
# plt.close('all')

# datapath = "../RR_data/p13/processed"
# files = [f.path for f in os.scandir(datapath)]

# results = np.zeros((4, len(files)), dtype=None)

# for i, f in enumerate(files):
#     if f == datapath +  r"\beatLog.npz":
#         pass
#     elif f == datapath + r"\info.npz":
#         pass
#     else:
#         data = np.load(f)
#         peaks = data["R_peaks"]
#         intervals= np.diff(peaks)
#         peaks = peaks[0:-1]

#     results=time_analysis(intervals)

# #         # results[0, i] = f.split(r"/")[0]
# #         results[1, i] = rmssd(intervals)
# #         results[2, i] = sdnn(intervals)
# #         results[3, i] = pnn50(intervals)

# #         print("rms: " + str(results[1, i]))
# #         print("sdnn: " + str(results[2, i]))
# #         print("pnn50: " + "{:.0%}".format(results[3, i]))
