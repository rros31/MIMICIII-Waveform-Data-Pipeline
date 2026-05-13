# -*- coding: utf-8 -*-
"""
Created on Tue May 17 16:00:20 2022

@author: cca78
"""

import numpy as np
import scipy.sparse as sp
import matplotlib.pyplot as plt


def detrend(intervals, param = 500):
    I = np.identity(len(intervals))
    D2 = sp.diags([1, -2, 1], [0, 1, 2], shape=(len(intervals) - 2, len(intervals))).toarray()
    mult = I - np.linalg.inv(I + param**2 * np.matmul(D2.T, D2))
    detrended = np.matmul(mult,intervals)

    return detrended

def remove_anomalies(intervals,
                     time_indices,
                     alpha=5.2 #Set by Lipponen et al
                     ):
    #adapted from Lipponen et al 2019

    drrs = intervals
    mrrs = sp.ndimage.median_filter(data, size=11)
    #Figure out how to apply this thresholding to vecor using numpy not slow loop
    for i in len(intervals):
        Th

    return amended_intervals, amended_indices

def quartile_deviation(data):
    Q1 = np.quantile(data,0.25)
    Q3 = np.quantile(data,0.75)
    QD = (Q3 - Q1) / 2

    return QD
