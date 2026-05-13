import sys
from pathlib import Path
import wfdb
import csv
import gzip
import matplotlib.pyplot as plt
import numpy as np
from wfdb import processing
import HRV
import pandas as pd
import datetime
import pickle
def split_epochsRR(RR_ints, window_size = 5*60, step_size = 30):
    cumulative_time = np.cumsum(RR_ints)
    start_times = np.arange(0,cumulative_time[-1]-window_size,step_size)


    start_indices = np.searchsorted(cumulative_time, start_times)
    end_indices = np.searchsorted(cumulative_time, start_times +window_size)

    
    windows = [RR_ints[start:end] for start, end in zip(start_indices, end_indices) if end <= len(RR_ints)]
    
    return windows

def split_epochsRT(R_times, window_size = 5*60, step_size = 5*60):
    start_times = np.arange(0,R_times[-1]-window_size,step_size)


    start_indices = np.searchsorted(R_times, start_times)
    end_indices = np.searchsorted(R_times, start_times +window_size)
    windows = [R_times[start:end] for start, end in zip(start_indices, end_indices) if end <= len(R_times)]

    return windows
def split_epcohs(R_times, RR_ints,window_size = 5*60, step_size = 5*60):
    start_times = np.arange(0,R_times[-1]-window_size,step_size)


    start_indices = np.searchsorted(R_times, start_times)
    end_indices = np.searchsorted(R_times, start_times +window_size)
    Rwindows = [R_times[start:end] for start, end in zip(start_indices, end_indices) if end <= len(R_times)]
    RRwindows = [RR_ints[start:end] for start, end in zip(start_indices, end_indices) if end <= len(RR_ints)]
    return {"R":Rwindows,"RR":RRwindows}



with open('Patient_Subset.pkl', 'rb') as file:
    records = pickle.load(file)

stay_ids = records.keys()

subject_id = records[stay_ids[0]].id
fprim =f'waveforms/{subject_id:06d}/'

Num_records = len(records[stay_ids[0]].records)
print(Num_records)

head = f'p000124-{records[stay_ids[0]].records[0]}'


hed = wfdb.rdheader(fprim+head, rd_segments=True)
segments = hed.seg_name
sections_lenghts= hed.seg_len


t_offset =0
all_segemnts = pd.DataFrame()
prevsig = []
for ii in range(1,len(segments)):
    print(segments[ii])
    if segments[ii] == "~":
        t_offset += sections_lenghts[ii]
    elif sections_lenghts[ii] < 37000:
        t_offset += sections_lenghts[ii]
    else:
        rname =fprim +segments[ii]
        segment_metadata = wfdb.rdheader(rname)

        
        fs = round(segment_metadata.fs)
        segment_data = wfdb.rdrecord(record_name=rname)
        chan = segment_metadata.sig_name.index("II")
        
        
        sig, fields = wfdb.rdsamp(rname, channels=[chan])

        prevsig = sig
        xqrs =processing.XQRS(sig=sig[:,0], fs=fields['fs'])
        xqrs.detect()
        if len(xqrs.qrs_inds) ==0:
            print("Retrying with No bandpass filter")
            xqrs.noFilter = True
            xqrs.detect()

        if len(xqrs.qrs_inds) ==0:
            xqrs.detect(sampfrom=np.where(np.isnan(sig[:,0]))[-1][-1]+1)
            
        R_times= xqrs.qrs_inds*1/(fields['fs'])
        RR_ints = np.diff(R_times)

        # #Break Into EPOCS
        temp = split_epcohs(R_times,RR_ints)
        epochs_RR = temp["RR"]
        epochs_RT = temp["R"]

        N = len(epochs_RR)
        freq = []
        DC = []
        all_epochs = pd.DataFrame()
        for jj in range(N):
            stress_metrics = HRV.process_all(epochs_RT[jj][:],epochs_RR[jj][:],0)

            stress_metrics = pd.DataFrame([stress_metrics])
            all_epochs = pd.concat([all_epochs, stress_metrics ], ignore_index=True)
            print(f"{jj}/{N}")

        timeVec = np.arange(0,N*5*60,5*60)
        all_epochs["Time"] = timeVec +np.ones(np.size(timeVec))*t_offset


        all_segemnts = pd.concat([all_segemnts,all_epochs])
        t_offset += sections_lenghts[ii]
    print("---------------------Segment Done-----------------------------------------")
    print(f"SEGMENT: {ii}/{len(segments)}")


# # print(fs)
# print(segment_metadata.base_date)
# start_seconds = 20
# n_seconds_to_load = 60
# sampfrom = fs * start_seconds
# sampto = fs * (start_seconds + n_seconds_to_load)

# 
# print(vars(segment_data))
# print(segment_data.base_time)
# print(type(segment_data.p_signal))

# sig, fields = wfdb.rdsamp(rname, channels=[2])
# print(sig)
# xqrs =processing.XQRS(sig=sig[:,0], fs=fields['fs'])
# xqrs.detect()

# # print(xqrs.qrs_inds)

# R_times= xqrs.qrs_inds*1/(fields['fs'])
# RR_ints = np.diff(R_times)

# #Break Into EPOCS
# temp = split_epcohs(R_times,RR_ints)
# epochs_RR = temp["RR"]
# epochs_RT = temp["R"]

# N = len(epochs_RR)
# freq = []
# DC = []
# all_epochs = pd.DataFrame()
# for i in range(N):

#     stress_metrics = HRV.process_all(epochs_RT[i][:],epochs_RR[i][:],0)

#     stress_metrics = pd.DataFrame([stress_metrics])
#     all_epochs = pd.concat([all_epochs, stress_metrics ], ignore_index=True)
#     print(f"{i}/{N}")

# timeVec = np.arange(0,N*5*60,5*60)
# plt.plot(timeVec,freq)
# plt.figure()
# plt.plot(timeVec,DC)

# print(stress_metrics)
# wfdb.plot_items(signal=sig, ann_samp=[xqrs.qrs_inds])

# plt.plot(segment_data.p_signal[:,2])
# plt.show()
#wfdb.plot_wfdb(record=segment_data,
#                time_units='seconds')
# """
#   Examples
#     --------
#     >>> import wfdb
#     >>> from wfdb import processing

#     >>> sig, fields = wfdb.rdsamp('sample-data/100', channels=[0])
#     >>> xqrs = processing.XQRS(sig=sig[:,0], fs=fields['fs'])
#     >>> xqrs.detect()

#     >>> wfdb.plot_items(signal=sig, ann_samp=[xqrs.qrs_inds])
# """