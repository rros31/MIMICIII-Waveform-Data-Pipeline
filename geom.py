# -*- coding: utf-8 -*-
"""
Created on Tue May 17 14:05:45 2022

@author: cca78
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
# import warnings
# warnings.simplefilter('ignore', np.RankWarning)
def geometric_analysis(intervals, 
                       baevsky_binwidth=50,
                       baevsky_root=True,
                       baevsky_median=True,
                       TINN_binwidth=(1000/128),
                       TINN_plot=False,
                       TINN_ax=None):
    
    #convert to ms if in seconds
    if intervals[-1] < 2:
        intervals = intervals * 1000
    
    baevsky = baevsky_index(intervals,
                            root = baevsky_root, 
                            median = baevsky_median,
                            binwidth = baevsky_binwidth)
    
    HRVi = triangular_index(intervals,
                            binwidth=TINN_binwidth)
    
    tinn = TINN(intervals,
                binwidth=TINN_binwidth,
                plot=TINN_plot,
                ax=TINN_ax)
    
    geom_results = {"BSI":baevsky,
                    "HRVi":HRVi,
                    "TINN":tinn}
    
    return geom_results

def bin_intervals(intervals, binwidth = 50, minbin=200, maxbin=2000):
    if intervals[0] < 2:
        intervals = intervals * 1000

    bins = np.arange(minbin,maxbin,binwidth)
    hist, bins = np.histogram(intervals, bins)

    return hist, bins

def baevsky_index(intervals, root=True, median=True, binwidth = 50):
    hist, bins = bin_intervals(intervals, binwidth = binwidth)
    mode = bins[np.argmax(hist)] - binwidth / 2
    if median:
        mode = np.median(intervals)

    mode_density = np.amax(hist) / len(intervals)
    MxDMn = np.amax(intervals) - np.amin(intervals)

    BSI = mode_density / (2 * mode * MxDMn)

    if root:
        BSI = np.sqrt(BSI)

    return BSI

def triangular_interp(intervals, binwidth=(1000/128), plot=True, ax=None):
    hist, bins = bin_intervals(intervals, binwidth=binwidth)
    bins = bins[1:]
    X = bins[np.argmax(hist)] + binwidth/2
    Y = np.amax(hist)
    valid_range = np.logical_and((bins >= np.amin(intervals)), (bins <= np.amax(intervals)))
    valid_indices = np.argwhere(valid_range)
    min_error = 1e10

    n_vec = np.arange(bins[valid_indices[0]] + binwidth/2, X + binwidth, binwidth)
    m_vec = np.arange(X, bins[valid_indices[-1]] + binwidth/2 + binwidth, binwidth)
    errors = np.zeros((len(n_vec), len(m_vec)))
    q = np.zeros(len(bins))

    #TODO: Remove rcond when pandas fixes it's cython build
    for i, n in enumerate(n_vec):
        q[:] = 0
        qn = np.polyval(np.polyfit([n, X], [0, Y], deg=1, rcond = 4e-16), bins[np.where(bins >= n)[0][0]:np.where(bins >= X)[0][0]])
        q[np.where(bins >= n)[0][0]:np.where(bins >= X)[0][0]] = qn

        for j, m in enumerate(m_vec):
            try:
                qm = np.polyval(np.polyfit([X,m], [Y,0], deg=1, rcond = 4e-16), bins[np.where(bins >= X)[0][0]: np.where(bins >= m)[0][0]])
                q[np.where(bins >= X)[0][0]: np.where(bins >= m)[0][0]] = qm
                errors[i, j] = np.sum((q[valid_range] - hist[valid_range]))**2
            except IndexError as e:
                print(e)
                #Save a biiiiig number to find the culprit later
                return[0, 100000]


    args = np.unravel_index(np.argmin(errors), errors.shape)
    n = n_vec[args[0]]
    m = m_vec[args[1]]

    if plot:
        if not ax:
            fig, ax = plt.subplots(1,1)
        ax.hist(bins[valid_range], bins[valid_range], weights=hist[valid_range])
        ax.plot([n, X], [0,Y])
        ax.plot([X, m], [Y,0])
        ax.set_xlabel("Interval (ms)")
        ax.set_ylabel("n")
        ax.set_title("Least-squares triangular fit")

    return [n, m]

def TINN(intervals, binwidth = (1000/128), plot=True ,ax=None):
    feet = triangular_interp(intervals, binwidth, plot, ax)
    index = np.diff(feet)[0]
    return index

def triangular_index(intervals, binwidth = 1000/128):
    hist, bins = bin_intervals(intervals, binwidth=binwidth)
    hrvi = len(intervals) / np.amax(hist)
    return hrvi




#Test_code


# # baevsky_index(sample_hrv_master)
# plt.figure()
# plt.hist(sample_hrv_master, bins)
