from re import S
import numpy as np
import HRV
import wfdb
from wfdb import processing
import pandas as pd
from scipy.signal import medfilt
from queries import MIMICQuery
from datetime import datetime
import neurokit2 as nk
import warnings
import matplotlib.pyplot as plt
class WaveformTools():

    def __init__(self,record):
        self.Rwindows = []
        self.RRwindows = []
        self.record = record
        self.id = record.id
        self.N_waveforms = len(record.records)

        self.paths = []
        self.path_index = 0

        self._get_record_paths()
        self.t_offset = 0
        self.fprim =f'waveforms/{record.id:06d}/'

        self.all_segements = pd.DataFrame()
    def _get_record_paths(self):
        for waveform in self.record.records[:]:
            self.paths.append(f"waveforms/{self.id:06d}/"+waveform[0].split('/')[-1])

       
   
        
    def _split_epcohs(self, R_times, RR_ints,window_size = 5*60, step_size = 5*60):
        start_times = np.arange(0,R_times[-1]-window_size,step_size)
        start_indices = np.searchsorted(R_times, start_times)
        end_indices = np.searchsorted(R_times, start_times +window_size)
        self.Rwindows = [R_times[start:end] for start, end in zip(start_indices, end_indices) if end <= len(R_times)]
        self.RRwindows = [RR_ints[start:end] for start, end in zip(start_indices, end_indices) if end <= len(RR_ints)]
        
    def _remove_ectopic_beats(self,R_times,outlier_tol=0.2):
        RR_ints = np.diff(R_times)
        mediainRR = medfilt(RR_ints,51)
        filtered_R_times = R_times
        for ii in range(len(RR_ints)-1):
            ectopic_bool = abs(RR_ints[ii]-mediainRR[ii]) > outlier_tol and abs(RR_ints[ii+1]-mediainRR[ii]) > outlier_tol
            if ectopic_bool:
                filtered_R_times[ii+1] =  (R_times[ii]+R_times[ii+2])/2

        return filtered_R_times
    def get_segment_datetime(self,segment_path=None):
        if segment_path is None:
            segment_path = self.paths[0]
        hed = wfdb.rdheader(segment_path, rd_segments=True)
        return datetime.combine(hed.base_date, hed.base_time)
    
    def get_record_deltaT(self,record1,record2):
        date1 = self.get_segment_datetime(segment_path=record1)
        date2 = self.get_segment_datetime(segment_path=record2)
        difference = date2 - date1
        return difference.total_seconds()

    def get_pleth_rr(self,pleth,f):
        #Inputs Pleth timeseries and returns detercted Rtimes
          # Sanitize input
        ppg_signal = nk.as_vector(pleth)
        methods = nk.ppg_methods(sampling_rate=f, method="elgendi", method_quality="templatematch")

        # Clean signal
        ppg_cleaned =nk. ppg_clean(
            ppg_signal,
            sampling_rate=f,
            method=methods["method_cleaning"],
            **methods["kwargs_cleaning"]
        )
        peaks_signal, info = nk.ppg_peaks(
                ppg_cleaned,
                sampling_rate=f,
                method=methods["method_peaks"],
                **methods["kwargs_peaks"]
            )
        
        return info["PPG_Peaks"]


    def process_segment_PPG(self,segment):
        rname = f"waveforms/{self.id:06d}/" + segment
        segment_metadata = wfdb.rdheader(rname)
        fs = round(segment_metadata.fs)
        segment_data = wfdb.rdrecord(record_name=rname)
        try:
            chan = segment_metadata.sig_name.index("PLETH")
        except ValueError:
            return pd.DataFrame([])
        
        sig, fields = wfdb.rdsamp(rname, channels=[chan])
        # R_times = self.get_pleth_rr(sig[:,0],fs)
        self.sig = sig[:,0]
        epochs = nk.epochs_create(sig[:,0],sampling_rate=fs,epochs_start=0,epochs_end=60*10)
        
    
        # nk.ppg_plot(ppg, info)
        hrv_df = pd.DataFrame([])
        
        # R_times=self.get_pleth_rr(ppg,fs)
        # self._split_epcohs(R_times, np.diff(R_times),window_size=5*60*fs, step_size =5*60*fs)
        # epochs = self.Rwindows
        self.last_epochs = epochs
        # print(epochs)
            
            
        # except:
        #     print("ERROR")
        #     return pd.DataFrame([])
        N=len(epochs)
        timeVec=[]
        epoch_time =0
        for ii in range(1,N+1):
                # print(ii)
                epoch_peaks = self.get_pleth_rr(epochs[f"{ii}"]['Signal'].values,fs)
                try:
                    # hrv_df = pd.concat([hrv_df,nk.hrv(epoch_peaks)])
                    Rtimes = epoch_peaks /fs
                    RR_times = np.diff(Rtimes)
                    # print(Rtimes)
                    # print(len(Rtimes))
                    self.Rtimes = Rtimes
                    self.RRtimes = RR_times
                    # print(len(RR_times))
                    hrv_met = HRV.process_all(Rtimes[:-1],RR_times,0)
                    hrv_df = pd.concat([hrv_df,pd.DataFrame([hrv_met])])
                    timeVec.append(epoch_time)
                    epoch_time+=60*10
                except Exception as error:
                    print(error)
                    epoch_time+=60*10
        N=len(hrv_df)
        timeVec = np.array(timeVec)
        hrv_df["Time"] = timeVec +np.ones(np.size(timeVec))*self.t_offset
        return hrv_df
        # RR_ints = np.diff(R_times)
        # # #Break Into EPOCS
        # self._split_epcohs(R_times,RR_ints)
        # epochs_RR = self.RRwindows 
        # epochs_RT = self.Rwindows

        # N = len(epochs_RR)
        # print(N)
        # all_epochs = pd.DataFrame()

            
        # for jj in range(N):
        #     try:
        #         # print(jj)
        #         stress_metrics = HRV.process_all(epochs_RT[jj][:],epochs_RR[jj][:],epochs_RR[jj][1])       
        #     except (IndexError,ZeroDivisionError) as e:
        #         print(e)
        #         stress_metrics ={"AC":0,
        #         "DC":0,
        #         "AC/DC": 0,
        #         "rmssd":0,
        #         "sdnn":0,
        #         "pnn50":0,
        #         "VLF":0,
        #         "LF":0,
        #         "HF":0,
        #         "LF/HF":0,
        #         "DFA_a1":0,
        #         "ANI":0,
        #         # "BSI":geom_metrics["BSI"],
        #         # "TINN":geom_metrics["TINN"],
        #         # "HRVi":geom_metrics["HRVi"],
        #         "duration":0,
        #         "num_beats":0
        #         }
        #     stress_metrics = pd.DataFrame([stress_metrics])
        #     all_epochs = pd.concat([all_epochs, stress_metrics ], ignore_index=True)
        #     print(f"{jj}/{N}")

        # timeVec = np.arange(0,5*N*60,5*60)
        
        # all_epochs["Time"] = timeVec +np.ones(np.size(timeVec))*self.t_offset

        
        # return all_epochs
    


    def process_segment(self,segment,libary):  
       
        rname = f"waveforms/{self.id:06d}/" + segment
        segment_metadata = wfdb.rdheader(rname)
        fs = round(segment_metadata.fs)
        segment_data = wfdb.rdrecord(record_name=rname)
        try:
            chan = segment_metadata.sig_name.index("II")
        except ValueError:
            return pd.DataFrame([])
        sig, fields = wfdb.rdsamp(rname, channels=[chan])
        if libary =='wfdb':
            xqrs =processing.XQRS(sig=sig[:,0], fs=fields['fs'])
            xqrs.detect()
            # if len(xqrs.qrs_inds) ==0 and len(np.where(np.isnan(sig[:,0]))[-1])>0:
            #     try:
            #         xqrs.detect(sampfrom=np.where(np.isnan(sig[:,0]))[-1][-1]+1)    
            #     except ValueError:
            #         pass
            if len(xqrs.qrs_inds) ==0:
                print(sig[1,0])
                print("Retrying with No bandpass filter")
                xqrs.noFilter = True
                xqrs.detect()

            if len(xqrs.qrs_inds) ==0 and len(np.where(np.isnan(sig[:,0]))[-1])>0:
                try:
                    # xqrs.noFilter = True
                    xqrs.detect(sampfrom=np.where(np.isnan(sig[:,0]))[-1][-1]+1)
                except ValueError:
                    pass   
            if len(xqrs.qrs_inds) ==0:
                print("Segment Failed")
                return pd.DataFrame([])
            
            R_times= xqrs.qrs_inds*1/(fields['fs'])
        elif libary == 'nk':
            ecg =sig[:,0]
            ecg[np.isnan(ecg)] = 0
            # df, info = nk.ecg_process(ecg,sampling_rate=fs)
            ecg_signal = nk.signal_sanitize(ecg)
            ecg_cleaned =  ecg_signal#nk.ecg_clean(ecg_signal, sampling_rate=fs, method="neurokit")
            instant_peaks, info = nk.ecg_peaks(
            ecg_cleaned=ecg_cleaned,
            sampling_rate=fs,
            method="neurokit",
            correct_artifacts=True,
            )

            R_times = info["ECG_R_Peaks"]
            R_times = R_times / fs 
            print(R_times)
        # R_times = self._remove_ectopic_beats(R_times)
        RR_ints = np.diff(R_times)
        # #Break Into EPOCS
        self._split_epcohs(R_times,RR_ints)
        epochs_RR = self.RRwindows 
        epochs_RT = self.Rwindows

        N = len(epochs_RR)
        print(N)
        all_epochs = pd.DataFrame()

            
        for jj in range(N):
            try:
                # print(jj)
                stress_metrics = HRV.process_all(epochs_RT[jj][:],epochs_RR[jj][:],epochs_RR[jj][1])       
            except (IndexError,ZeroDivisionError) as e:
                print(e)
                stress_metrics ={"AC":0,
                "DC":0,
                "AC/DC": 0,
                "rmssd":0,
                "sdnn":0,
                "pnn50":0,
                "VLF":0,
                "LF":0,
                "HF":0,
                "LF/HF":0,
                "DFA_a1":0,
                "ANI":0,
                # "BSI":geom_metrics["BSI"],
                # "TINN":geom_metrics["TINN"],
                # "HRVi":geom_metrics["HRVi"],
                "duration":0,
                "num_beats":0
                }
            stress_metrics = pd.DataFrame([stress_metrics])
            all_epochs = pd.concat([all_epochs, stress_metrics ], ignore_index=True)
            print(f"{jj}/{N}")

        timeVec = np.arange(0,5*N*60,5*60)
        
        all_epochs["Time"] = timeVec +np.ones(np.size(timeVec))*self.t_offset

        
        return all_epochs

    def process_HRV_all_epochs(self,libary='wfdb',signal="ppg"):
        hed = wfdb.rdheader(self.paths[self.path_index], rd_segments=True)
        segments = hed.seg_name
        sections_lenghts= hed.seg_len
        
        for ii in range(1,len(segments)):
            if segments[ii] == "~":
                self.t_offset += sections_lenghts[ii]*(1/125)
            elif sections_lenghts[ii] < 112500: #37000
                self.t_offset += sections_lenghts[ii]*(1/125)
            elif signal == "ecg":
                self.all_segements = pd.concat([self.all_segements,self.process_segment(segments[ii],libary)],ignore_index=True)
                self.t_offset += sections_lenghts[ii]*(1/125)
            elif signal == "ppg":
                self.all_segements = pd.concat([self.all_segements,self.process_segment_PPG(segments[ii])],ignore_index=True)
                self.t_offset += sections_lenghts[ii]*(1/125)
            else:
                self.t_offset += sections_lenghts[ii]*(1/125)
                warnings.warn("Unable to process segment")
            print("---------------------Segment Done-----------------------------------------")
            print(f"SEGMENT: {ii}/{len(segments)}")
            
        
        
        if self.path_index !=  self.N_waveforms-1:
            self.t_offset += self.get_record_deltaT(self.paths[self.path_index],self.paths[self.path_index+1])
            self.path_index += 1
            self.process_HRV_all_epochs(libary=libary,signal=signal)
