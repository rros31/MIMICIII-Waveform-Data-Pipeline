import pickle
import wave
from matplotlib.backends import _QT_FORCE_QT5_BINDING
import matplotlib.pyplot as plt
import numpy as np
from sympy import Q, count_ops
from WaveformTools import WaveformTools
from drugProcess import DrugData
from datetime import datetime
from scipy.ndimage import median_filter
from queries import MIMICQuery
from scipy.interpolate import interp1d

from scipy.signal import butter, filtfilt, lfilter
import pandas as pd


from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

def outlier_filter(time,signal,N=15):
    #Remove Points 3std from moving mean
    
    av_sig = median_filter(signal,size=N)
    std = np.std(av_sig)
    new_time = time[abs(signal-av_sig)<10*std]
    new_sig = signal[abs(signal-av_sig)<10*std]
    
    return new_time, new_sig

with open('Patient_Subset.pkl', 'rb') as file: 
    records = pickle.load(file)

%matplotlib qt

# Now `matching_rows` contains all the filtered data

with open('Patient_Subset.pkl', 'rb') as file: 
    records = pickle.load(file)

#[10, 25,73, 82, 84(More Waveforn Files), 90(Great) 102  103 (105,109(Good Ras not Qunat)]\\
# 
num =   90
stay_ids = list(records.keys())

# df = dd.read_csv(s'M3_Clincial/CHARTEVENTS.csv')

# chart  = df[df["HADM_ID"]==stay_ids[num]].compute()

# print(chart)
# chunksize = 1000000
# count=0
# QuerryRes = pd.DataFrame([])
# for chunk in pd.read_csv('M3_Clincial/CHARTEVENTS.csv', chunksize=chunksize):
#     print(count)
#     count+=1
# #     QuerryRes = pd.concat([QuerryRes, chunk[chunk["HADM_ID"].isin(stay_ids)]],ignore_index=True)
querry = MIMICQuery(import_filt_chart=True)

while 1:
    try:
        sedscore = querry.sed_score_querry(stay_ids[num])

        sedtype = querry.sed_score_lookup[sedscore["ITEMID"].iloc[0]]
        print(num)
        break
        
    except:
        num +=1



waveform_tools=WaveformTools(records[stay_ids[num]])
waveform_tools.process_HRV_all_epochs(libary='nk')


start_time = waveform_tools.get_segment_datetime()
sed_times = []
sed_num_score = []
for ii in range(len(sedscore)):
    sed_times.append((datetime.strptime(sedscore["CHARTTIME"].iloc[ ii], "%Y-%m-%d %H:%M:%S") -start_time).total_seconds())
    sed_num_score.append(sedscore["VALUENUM"].iloc[ii])

timeend = waveform_tools.all_segements["Time"].iloc[-1]


#----------------------------------------------------------------------------------
plt.close('all')
timeend= 450000
N=10
print(sedtype)

propQuerry = querry.propofol_query(stay_ids[num])
records[stay_ids[num]].drugChart= propQuerry["data"]
starttime = waveform_tools.get_segment_datetime()
drug_data = DrugData(records[stay_ids[num]],starttime)
sedative = drug_data.extract_sedative(datatype=propQuerry["datatype"])

# waveform_tools.all_segements["Garmin"] = waveform_tools.all_segements["HRV_MeanNN"]/(waveform_tools.all_segements["HRV_LF"]*waveform_tools.all_segements["HRV_HF"])
plt.figure()
metric = "sdnn"
plt.subplot(2,1,1)
met_plot = waveform_tools.all_segements[waveform_tools.all_segements[metric] != 0]
met_plot = met_plot[np.isnan(met_plot[metric])==0]

tp, sp = outlier_filter(met_plot["Time"],met_plot[metric])
plt.plot(tp,sp,'o')
plt.xlim((0,timeend))
plt.plot(tp,np.convolve(sp,np.ones(N)/N,mode ='same'))
plt.ylabel(metric)
plt.legend(["Unfiltered","N=50 MA"])
plt.subplot(2,1,2)
plt.plot(sed_times,sed_num_score,'o',markersize=10)
plt.xlim((0,timeend))



# # Open a file and use dump() 
# with open('P25.pkl', 'wb') as file: 
      
#     # A new file will be created 
#     pickle.dump(waveform_tools, file)

plt.figure()
Np = 4


plt.subplot(Np,1,1)
metric = "sdnn"
met_plot = waveform_tools.all_segements[waveform_tools.all_segements[metric] != 0]
met_plot = met_plot[np.isnan(met_plot[metric])==0]
tp, sp = outlier_filter(met_plot["Time"],met_plot[metric])


plt.plot(tp,sp,'o')
plt.xlim((0,timeend))
plt.plot(tp,np.convolve(sp,np.ones(N)/N,mode ='same'))
plt.ylabel(metric)
plt.legend(["Unfiltered","N=50 MA"])

interp_func_HRV = interp1d(tp, sp, kind='linear', fill_value="extrapolate")
plt.subplot(Np,1,2)
metric = "num_beats"
met_plot = waveform_tools.all_segements[waveform_tools.all_segements[metric] != 0]
met_plot = met_plot[np.isnan(met_plot[metric])==0]
tp, sp = outlier_filter(met_plot["Time"],met_plot[metric])
plt.plot(tp,sp,'o')
plt.xlim((0,timeend))
plt.plot(tp,np.convolve(sp,np.ones(N)/N,mode ='same'))
plt.ylabel(metric)
plt.legend(["Unfiltered","N=50 MA"])

plt.subplot(Np,1,3)
plt.plot(sed_times,sed_num_score,'o',markersize=10)
plt.xlim((0,timeend))
plt.ylabel("Rass Scores")

plt.subplot(Np,1,4)
plt.plot(sedative["Time"],sedative["Rate"])
plt.ylabel("Propfol Infusion Rate [mg/min]")
plt.xlim((0,timeend))
plt.xlabel("Time s")

HR = waveform_tools.all_segements["num_beats"]/15

sampling_rate = 1/(15*60)  # Sampling rate in Hz (for example, 1 sample per second if HR is calculated every second)
cutoff_frequency = 0.000001 # Cutoff frequency in Hz; adjust based on your data needs

# Create a Butterworth high-pass filter
b, a = butter(N=2, Wn=[cutoff_frequency], btype='highpass', fs=sampling_rate)
window_size = 100

# Apply the high-pass filter to the HR data
heart_rate_filtered = filtfilt(b, a, HR )
plt.figure()
plt.plot(heart_rate_filtered)
HR = heart_rate_filtered
ANI = waveform_tools.all_segements["ANI"]
HF = waveform_tools.all_segements["HF"] 
Time = waveform_tools.all_segements["Time"] 
HFi =0.5/HF
ANIi = 5000/ANI

A=1
B=1
C=1
Stress_ANI=  A*HR*ANIi/(B*HR+C*ANI)
Stress_HF =A*HR*HFi/(B*HR+C*HFi)

plt.figure()
plt.subplot(3,1,1)
plt.plot(Time,Stress_ANI)
plt.plot(Time,np.convolve(Stress_ANI,np.ones(N)/N,mode ='same'))
plt.xlabel("Time s")
plt.ylabel("")
plt.subplot(3,1,2)
plt.plot(Time,Stress_HF)
plt.plot(Time,np.convolve(Stress_HF,np.ones(N)/N,mode ='same'))

plt.subplot(3,1,3)
# plt.plot(Stress_HF)
plt.plot(sed_times,sed_num_score,'o',markersize=10)
start_time = 0
end_time = timeend
sed_times = np.array(sed_times)
sed_num_score = np.array(sed_num_score)
# Filter sed_times to include only values within the specified interval
filt_Sed_scores = sed_num_score[(sed_times >= start_time) & (sed_times <= end_time)]
filtered_sed_times = sed_times[(sed_times >= start_time) & (sed_times <= end_time)]



metric = "num_beats"
met_plot = waveform_tools.all_segements[waveform_tools.all_segements[metric] != 0]
met_plot = met_plot[np.isnan(met_plot[metric])==0]
tp, sp = outlier_filter(met_plot["Time"],met_plot[metric])

sp = np.convolve(sp,np.ones(N)/N,mode ='same')
interp_func = interp1d(tp, sp, kind='linear', fill_value="extrapolate")

interpolatedHRV = interp_func_HRV(filtered_sed_times)
interpolated_hr = interp_func(filtered_sed_times)
# Perform linear regression
filt_Sed_scores = np.array(filt_Sed_scores).reshape(-1, 1)  # Reshape for scikit-learn
interpolated_hr = np.array(interpolated_hr)  # Ensure it's a NumPy array
interpolatedHRV = np.array(interpolatedHRV) 
model = LinearRegression()
model.fit(filt_Sed_scores, interpolated_hr)

# Get the predicted values
best_fit_line = model.predict(filt_Sed_scores)
# Calculate R^2
r2 = r2_score(interpolated_hr, best_fit_line)

model2 = LinearRegression()
model2.fit(filt_Sed_scores, interpolatedHRV)
best_fit_line2 = model2.predict(filt_Sed_scores)
r22 = r2_score(interpolatedHRV, best_fit_line2)
# Plot the data points

plt.figure()
plt.plot(filt_Sed_scores, interpolated_hr, 'o', label='Data Points')

# Plot the line of best fit
plt.plot(filt_Sed_scores, best_fit_line, 'r-', label=f'Best Fit (R² = {r2:.2f})')

# Add labels, title, and legend
plt.xlabel('Sedation Scores')
plt.ylabel('Interpolated HR')
plt.title('Interpolated HR vs. Sedation Scores with Best Fit Line')
plt.legend()

# Show the plot


plt.figure()
plt.plot(filt_Sed_scores, interpolatedHRV, 'o', label='Data Points')
plt.plot(filt_Sed_scores, best_fit_line2, 'r-', label=f'Best Fit (R² = {r22:.2f})')
plt.xlabel("SedScores")
plt.ylabel("SDNN")
plt.legend()
plt.show()