# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 09:27:15 2022

@author: cca78

PRSA.py

Functions to perform phase-rectified signal averaging as outlined in Bauer et al
2006 (DOI: 10.1016/j.physa.2005.08.080). Parameters T and L are as described
in that paper. PRSA information is used to calculate Acceleration and Deceleration
Capacity as outlined in Bauer et al's other 2006 belter (DOI:10.1016/S0140-6736(06)68735-7).
Parameter s is as defined in this paper, which sets it at 2.



For quick reference:
    L should be longer than the period of the slowest frequency periodicity you
        would like to detect
    T tunes the frequencies to which the process is the most sensitive - f_max ~= 1 / (2.7T)
    s scale of haar wavelet function - how many points either side of the acceleration to
        include in your calculation of capacity. Set at 2 to match Bauer's definition'

    Convenience function AC_DC performs all steps and returns AC, DC, and
    a dict of intermediate results
"""
import numpy as np
# import matplotlib.pyplot as plt
from scipy.signal import lfilter
from os import scandir


def find_anchors(data, T=5, L=20):
    """ Find acceleration/deceleration acceleration for phase-rectified signal
    averaging. Parameters T & L as outlined in module docstring.

    Inputs:
        data: 1d array of nonstationary signal to be analysed
        T: Width of averaging window applied before anchor picked
        L: Length of window either side of anchor to be averaged.

    Outputs:
        acceleration_anchors: Points following a signal increase in magnitude
        deceleration_anchors: Points following a signal decrease in magnitude
    """

    if (T==1):
        data_diff = np.diff(data)
        A_D = np.insert(-np.sign(data_diff),0,0)
        A_D[:L] = np.nan
        A_D[-L:] = np.nan

    else:
        data_flipped = np.flip(data)

        ascending = lfilter(np.ones(T) / T, 1, data)
        descending = np.flip(lfilter(np.ones(T) / T, 1,data_flipped))

        #NAN out warmup periods
        warmup = max(L, T)
        ascending[:warmup - 1] = np.nan
        descending[-1 - warmup:] = np.nan

        A_D = np.sign(ascending - descending)

    acceleration_anchors = np.argwhere(A_D > 0)[:,0]
    deceleration_anchors = np.argwhere(A_D < 0)[:,0]

    return acceleration_anchors, deceleration_anchors


def PRSA(data, anchors, L=20):
    """ Align all anchor slices in a given vector and average. Note: behaviour if
    given anchor points within L indices of either end of the vector is not guaranteed.

    Inputs:
        data: 1d array of nonstationary signal to be analysed
        anchors: 1d array of anchor points to analyse
        L: Length of window either side of anchor to be averaged.

    Outputs:
        prsa: averaged waveform
        anchorslices: all slices in an mxn array, where n= 2L and m = len(anchors)
    """

    prsa = np.zeros(2 * L)

    anchorslices = np.zeros([len(anchors), 2*L])
    for i, k in enumerate(anchors):
        anchorslices[i, :] = data[k - L + 1: k + L + 1]

    prsa = np.mean(anchorslices, 0)
    # for index in anchors:
    #     prsa = np.mean()
    return prsa, anchorslices


def capacity(prsa, s=3, L=20):
    """ Calculate acceleration and deceleration capacity from a PRSA waveform.

    Inputs:
        prsa: 1d array of phase-rectified-signal-average to be analysed
        s: scale factor of Haar wavelet (how far either side of anchor to calculate capacity)
        L: Length of window either side of anchor to be analyzed (included here in case s>L)

    Outputs:
        capacity: capacity (acceleration or deceleration)
    """
    scale = min(s, L)
    capacity = np.sum(prsa[L:L + scale]) - np.sum(prsa[L - scale - 1:L - 1])
    capacity = capacity / (2*scale)
    return capacity


def AC_DC(data, T=3, L=20, s=2):
    """ Given a signal vector and the parameters outlined by Bauer, performs
    PRSA and calculates AC/DC, outputting result and a dict of intermediate
    data

    Inputs:
        data: 1d array of nonstationary signal to be analysed
        T: Width of averaging window applied before anchor picked
        L: Length of window either side of anchor to be analyzed (included here in case s>L)
        s: scale factor of Haar wavelet (how far either side of anchor to calculate capacity)

    Outputs:
        AC: Accleration capacity
        DC: Deceleration capacity
        info: Dict of intermediate data:
            PRSA Acceleration - averaged acceleration waveform
            PRSA Deceleration - averaged deceleration waveform
            Acceleration Anchors - Anchor points for accelerations
            Deceleration Anchors - Anchor points for decelerations

    *Note: to get array of all averaged slices, you will need to run the PRSA
    function specifically.
    """
    acc, dec = find_anchors(data, T, L)
    prsa_acc = PRSA(data, acc, L)[0]
    prsa_dec = PRSA(data, dec, L)[0]

    AC = capacity(prsa_acc, s, L)
    DC = capacity(prsa_dec, s, L)

    info = {"PRSA Acceleration":prsa_acc,
            "PRSA Deceleration":prsa_dec,
            "Acceleration Anchors":acc,
            "Deceleration Anchors":dec}

    return AC, DC, info







# # Test code
# plt.close('all')

# datapath = "../RR_data/p13/processed"
# files = [f.path for f in scandir(datapath)]

# s = 2
# L = 50
# T = 1


# for i, f in enumerate(files):
#     if f == datapath +  r"\beatLog.npz":
#         pass
#     elif f == datapath + r"\info.npz":
#         pass
#     else:

#         data = np.load(f)

#         peaks = data["R_peaks"]
#         if len(peaks) < 2*L + 20:
#             pass
#         else:
#             intervals= np.diff(peaks) * 1000 #convert to ms for comparable metrics
#             peaks = peaks[0:-1] * 1000 #convert to ms for comparable metrics

#             AC, DC, info = AC_DC(intervals, T, L, s)

# #             prsa_acc = info["PRSA Acceleration"]
# #             prsa_dec = info["PRSA Deceleration"]
#             acc = info["Acceleration Anchors"]
#             dec = info["Deceleration Anchors"]

# #             a_slices = PRSA(intervals, acc, L)[1]
# #             d_slices = PRSA(intervals, dec, L)[1]

# #             # plt.figure()
# #             # plt.plot(a_slices.T)
# #             # plt.plot(prsa_acc, linewidth=3)

# #             # plt.figure()
# #             # plt.plot(d_slices.T)
# #             # plt.plot(prsa_dec, linewidth=3)

# #             # plt.figure()
# #             # plt.plot(prsa_acc)
# #             # plt.plot(prsa_dec)

#             plt.figure()
#             plt.title(f)
#             plt.plot(intervals)
#             plt.plot(acc, intervals[acc], 'rx')
#             plt.plot(dec, intervals[dec], 'bx')


# #             print("AC: " + str(AC))
# #             print("DC: " + str(DC))
