# -*- coding: utf-8 -*-
"""
HRV.py
Created on Tue Mar  8 15:58:50 2022

Created to reduce coupling between ECG file handling and R peak recognition, GUI,
and then fancy HRV stuff. Hopefully, it did that.

The HRV class keeps hold of all the HRV metrics for an Epoch.
Each metric has it's own function.
All HRV metrics take a vector of time indexes of heartbeats.
@author: cca78
"""
from scipy.signal import resample, lombscargle, welch
from scipy.interpolate import interp1d
from scipy.integrate import simpson
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import os

sns_deep = sns.color_palette("muted", as_cmap=True)

def interpolate_peaks(time_indices, intervals, desired_fs, method='cubic', window="blackman"):

    scipy_methods = ['linear',
                     'nearest',
                     'nearest-up',
                     'zero',
                     'slinear',
                     'cubic',
                     'previous',
                     'next']

    if method in scipy_methods:

        func = interp1d(time_indices, intervals, kind=method)
        duration = time_indices[-1] - time_indices[0]
        t = np.linspace(time_indices[0], time_indices[-1], int(duration * desired_fs), endpoint=False)

        return func(t), t

    elif method == "resample":
        duration = time_indices[-1] - time_indices[0]
        num_samples = int(duration * desired_fs)

        resampled = resample(intervals, num_samples, t=time_indices, window=window)

        return resampled

    else:
        print("Interpolation method unsupported")


def _welch(intervals, fs):
    f, ps = welch(intervals, fs=fs, window = "blackman", nperseg=300*fs,  return_onesided = True)
    return ps, f

def lomb_scargle(time_indices, intervals):
    pass
    # minfreq = 0.01
    # maxfreq = np.pi
    # freqs = np.linspace(minfreq, maxfreq, 100000)
    # periodogram = lombscargle(time_indices, intervals, freqs, normalize=False, precenter=True)

    # return periodogram, (freqs / (2*np.pi))

def freq_bands(psd, freqs, lims={"VLF": [0.0033, 0.04],
                                 "LF": [0.04, 0.15],
                                 "HF": [0.15,0.4]}):

    df = freqs[1] - freqs[0]
    LF_indices = argrange(freqs, lims["LF"])
    HF_indices = argrange(freqs, lims["HF"])
    VLF_indices = argrange(freqs, lims["VLF"])

    LF = simpson(psd[LF_indices], dx=df)
    HF = simpson(psd[HF_indices], dx=df)
    VLF = simpson(psd[VLF_indices], dx=df)

    return {"VLF":VLF,
            "LF":LF,
            "HF":HF,
            "LF/HF":LF/HF}

def freq_analysis(time_indices,
                  intervals,
                  interp_fs = 4,
                  interp_method='cubic',
                  window='blackman',
                  lims={"VLF": [0.00, 0.04],
                        "LF":[0.04, 0.15],
                        "HF":[0.15,0.4]},
                  plot_spectrum=False):
    # Interpolate onto regular sampling grid
    resampled_intervals = interpolate_peaks(time_indices, intervals, desired_fs=interp_fs)

   # ls = lomb_scargle(time_indices, intervals)
    welch = _welch(resampled_intervals[0], interp_fs)

    welch_bands = freq_bands(welch[0], welch[1], lims)
    #ls_bands = freq_bands(ls[0], ls[1], lims)

    if plot_spectrum:
        fig, axs = plt.subplots(1,2)
        ax = axs.ravel()
        ax[0].plot(welch[1], welch[0], label="Welch Spectrum")
        ax[0].set_title("Welch PSD")
        ax[0].set_xlim([0, 0.5])
        ax[1].plot(ls[1], ls[0], label="Lomb-Scargle Periodogram")
        ax[1].set_title("Lomb-scargle PSD")
        ax[1].set_xlim([0,0.5])
        fig.suptitle("Frequency Results")

        VLF_indices = argrange(welch[1], lims["VLF"])
        LF_indices = argrange(welch[1], lims["LF"])
        HF_indices = argrange(welch[1], lims["HF"])
        welch_indices = [VLF_indices,
                         LF_indices,
                         HF_indices]

        # #stretch out area by 1 index for shading t
        # for indices in welch_indices:
        #     stretched_indices.append([indices[0] - 1, indices[1]])
        # welch_indices = stretched_indices

        VLF_indices = argrange(ls[1], lims["VLF"])
        LF_indices = argrange(ls[1], lims["LF"])
        HF_indices = argrange(ls[1], lims["HF"])
        ls_indices = [VLF_indices,
                      LF_indices,
                      HF_indices]

        for i in range(len(welch_indices)):

            ax[0].fill_between(welch[1][welch_indices[i]],
                               welch[0][welch_indices[i]],
                               color = sns_deep[i])
            ax[1].fill_between(ls[1][ls_indices[i]],
                               ls[0][ls_indices[i]],
                               color = sns_deep[i])
    else:
        ax = None

    return {"welch_bands":welch_bands,
            #"ls_bands":ls_bands,
            #"ls":ls,
            "welch":welch,
            "axes":ax}



def argrange(data, _range):
    ind = np.argwhere(np.logical_and(data >= np.amin(_range), data <= np.amax(_range)))[:,0]

    #stretch indices to allow back-to-back slices when boundary doesn't fall on limit
    if ind[0] != np.amin(_range):
        ind = np.insert(ind, 0, ind[0] - 1)

    return ind
# # Test code
# plt.close('all')

# datapath = "../RR_data/p13/processed"
# files = [f.path for f in os.scandir(datapath)]

# for i, f in enumerate(files):
#     if f == datapath +  r"\beatLog.npz":
#         pass
#     elif f == datapath + r"\info.npz":
#         pass
#     elif f == datapath + r"\Abnormal_Procedure_End_1022.4s.npz":
#         pass
#     else:
#         data = np.load(f)

#         peaks = data["R_peaks"]
#         intervals= np.diff(peaks)
#         peaks = peaks[0:-1]

#         results = freq_analysis(peaks, intervals)

#         ls, freqs = lomb_scargle(peaks, intervals)

#         interped, t_interp = interpolate_peaks(peaks, intervals, 4)
#         # resampled = interpolate_peaks(peaks, intervals, 4, method="resampled")

#         plt.figure()
#         plt.plot(peaks, intervals, label="intervals")
#         plt.plot(t_interp, interped, label="upsampled (cubic)")
#         # plt.plot(t_interp, resampled, label="resampled")
#         plt.legend()



#         psd, f = _welch(interped, fs=4)

#         plt.figure()
#         plt.plot(freqs, ls, label = "lomb")
#         plt.plot(f, psd, label = "welch")
#         plt.legend()

#         lomb = freq_bands(ls,freqs)

#         wch = freq_bands(psd,f)

#         agreement = lomb["LF/HF"] / wch["LF/HF"]
#         print(agreement)
