# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 16:23:34 2022

@author: cca78
"""

# from processed_analysis.HRV_freq import *
# from processed_analysis.HRV_time import *
# from processed_analysis.HRV_geom import *
# from processed_analysis.PRSA import *
# from processed_analysis.patients import *
# from processed_analysis.epochs import *
# from processed_analysis.results_df import *
# from processed_analysis.dfa import dfa

import freq
import time_metrics as time
import dfa
import data_cleaning
import geom
from epochs import *
from patients import *
import PRSA
import ANI

from multiprocessing import Pool

import os
import re

import numpy as np
import scipy.sparse as sp

import results_df

# import warnings
# warnings.simplefilter('ignore', np.RankWarning)
# warnings.filterwarnings('ignore', message='nperseg = ')

class progress_counter(object):
    def __init__(self,
                 patient_list):
        self.increment = 1 / len(patient_list)
        self.counter = 0
        
    def increment_counter(self):
        self.counter += self.increment
        
    def print_count(self): 
        print("{:.0%}".format(self.counter))
        
    def return_count(self):
        return self.counter
        
        

def process_all(time_indices,
                intervals,
                event_offset,
                freq_lims = {"VLF": [0, 0.04],
                             "LF": [0.04, 0.15],
                             "HF": [0.15, 0.4]},
                plot_spectrum=False,
                plot_dfa=False):
    #NOTE: currently uses welch bands by default- could amend to lomb_scargle


    length_before_trim = len(intervals)
    intervals = np.trim_zeros(intervals)
    length_after_trim = len(intervals)
    trimmed_zeroes = length_before_trim - length_after_trim

    if trimmed_zeroes:
        time_indices = np.delete(time_indices, np.arange(trimmed_zeroes))

    if np.any(intervals < 0):
        pass

    #Take a 120s slice of intervals for time metrics
    time_start = np.argwhere(time_indices > (time_indices[0] + event_offset))[0,0]
    try:
        time_finish = np.argwhere(time_indices > (time_indices[0] + event_offset + 120))[0,0]
    except IndexError:
        time_finish = len(time_indices) - 1
        # print("Warning: Recording less than 120s")

    AC, DC, acdc_info = PRSA.AC_DC(intervals)
    time_metrics = time.time_analysis(intervals[time_start:time_finish])
    freq_metrics = freq.freq_analysis(time_indices, intervals, plot_spectrum=plot_spectrum, lims=freq_lims)
    dfa_metrics = dfa.dfa(intervals, time_indices, plot=plot_dfa)
    try:
        ani = ANI.ani_analyis(intervals)
    except ValueError:
        ani = 0
    # geom_metrics = geom.geometric_analysis(intervals)

    #geom_metrics = { "BSI":0,"TINN":0,"HRVi":0}
    
    duration = time_indices[-1] - time_indices[0]
    num_beats = len(intervals)

    return {"AC":AC,
            "DC":DC,
            "AC/DC": AC / DC,
            "rmssd":time_metrics["rmssd"],
            "sdnn":time_metrics["sdnn"],
            "pnn50":time_metrics["pnn50"],
            "VLF":freq_metrics["welch_bands"]["VLF"],
            "LF":freq_metrics["welch_bands"]["LF"],
            "HF":freq_metrics["welch_bands"]["HF"],
            "LF/HF":freq_metrics["welch_bands"]["LF/HF"],
            "DFA_a1":dfa_metrics["coeffs"]["alpha_1"][1],
            "ANI":ani,
            # "BSI":geom_metrics["BSI"],
            # "TINN":geom_metrics["TINN"],
            # "HRVi":geom_metrics["HRVi"],
            "duration":duration,
            "num_beats":num_beats
            }
    
def run_hrv_analysis(data_directory = "//file/Usersc$/cca78/Home/My Documents/Work/Research Projects/R-R/Analysis/RR_data"):
    
    patient_list = patients([f.path for f in os.scandir(data_directory) if f.is_dir()])
    _results = results_df.results()
    processed_epoch_names = []
    prog_counter = progress_counter(patient_list)
        
    # Data structure - 1 dataframe per metric. Combine into multisheet csv offline.
    # 1 Row per patient trial, with another row added if trial comes to premature
    # end (indicated by ANE stamp)
    
    for patient in patient_list:
        subdirs = [f.path for f in os.scandir(patient) if f.is_dir()]
        
        if (patient + "\processed") not in subdirs:
            print(patient + " is unprocessed")
        else:
            # print("processing " + patient)
            patient_number = patient.split("\\")[-1].lstrip('p')
            _results.add_row(patient_number)
            processed_epochs = epochs([f.path for f in os.scandir(patient + "\processed")])
    
    
            for epoch in processed_epochs:
                processed_epoch_names.append(epoch.split("\\")[-1])
    
            infopath = patient + "\processed\info.npz"
            if not os.path.isfile(infopath):
                print(patient + " has processed epochs but no saved beatlog")
            else:
                patient_info = np.load(patient + "\processed\info.npz")
                tags = patient_info["tags"]
    
                for epoch in tags:
                    archive_name = epoch.replace(" ", "_") + ".npz"
                    tagtype = epoch.rstrip('0123456789.s ')
    
                    if archive_name in processed_epoch_names:
    
                        data = np.load(patient + r"\processed\\" + archive_name)
                        peaks = data["R_peaks"]
                        intervals= data["intervals"]
                        if tagtype == "Abnormal Procedure End":
                            _results.carraige_return(patient_number)
                        elif (peaks[-1] - peaks[0]) < 150:
                            print(epoch + " is too short to process")
                        else:
                            metrics = process_all(peaks, intervals, 30)
                            _results.store_timestamp_results(metrics, tagtype, patient_number)
                            
        prog_counter.increment_counter()
        prog_counter.print_count()

    _results.finish()
    return _results




def sliding_window_metrics(data, time_indices, window_size = 120):
    #TODO: matrix-ise these operations

    results = {"AC":np.zeros(len(data)),
                "DC":np.zeros(len(data)),
                "AC/DC": np.zeros(len(data)),
                "rmssd":np.zeros(len(data)),
                "sdnn":np.zeros(len(data)),
                "pnn50":np.zeros(len(data)),
                "VLF":np.zeros(len(data)),
                "LF":np.zeros(len(data)),
                "HF":np.zeros(len(data)),
                "LF/HF":np.zeros(len(data)),
                "DFA_a1": np.zeros(len(data)),
                "duration":np.zeros(len(data)),
                "num_beats":np.zeros(len(data))
                }

    target = 0
    print_freq = 1
    for i in range(len(data)):
        try:
            window_length = np.argwhere(time_indices > (time_indices[i] + window_size))[0,0] - i
        except IndexError:
            return results
        metrics = process_all(time_indices[i:i + window_length], data[i:i + window_length], 0)

        for key, metric in metrics.items():
            results[key][i] = metric

        progress = i / len(data)


        # if progress > target:
        print("{:%} complete".format(progress))
            # target += print_freq

    return results

# run_hrv_analysis(prog_callback)
