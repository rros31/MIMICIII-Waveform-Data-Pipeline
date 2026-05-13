import pickle
import wave
from matplotlib.backends import _QT_FORCE_QT5_BINDING
import matplotlib.pyplot as plt
import numpy as np
from WaveformTools import WaveformTools
from drugProcess import DrugData
from datetime import datetime

from queries import MIMICQuery




with open('Patient_Subset.pkl', 'rb') as file: 
    records = pickle.load(file)

num =   268
stay_ids = list(records.keys())




Num_records = len(records[stay_ids[num]].records)
print(Num_records)

waveform_tools=WaveformTools(records[stay_ids[num]])
querry = MIMICQuery()

propQuerry = querry.propofol_query(stay_ids[num])
records[stay_ids[num]].drugChart= propQuerry["data"]

starttime = waveform_tools.get_segment_datetime()
drug_data = DrugData(records[stay_ids[num]],starttime)
sedative = drug_data.extract_sedative(datatype=propQuerry["datatype"])
final_time = sedative["Time"][-1]
waveform_tools.process_HRV_all_epochs()





# analgesics = querry.analgesic_querries(stay_ids[num])
%matplotlib qt 
N=10
plt.figure()
plt.subplot(3,1,1)
plt.plot(sedative["Time"],sedative["Rate"])
plt.ylabel("Propfol Infusion Rate [mg/min]")
plt.xlim((0,final_time))
plt.subplot(3,1,2)
waveform_tools.all_segements["ANI"][np.isnan(waveform_tools.all_segements["ANI"])]=0
ANIplot = waveform_tools.all_segements[waveform_tools.all_segements["ANI"] != 0]
plt.plot(ANIplot["Time"],ANIplot["ANI"],'o')
plt.plot(ANIplot["Time"],np.convolve(ANIplot["ANI"],np.ones(N)/N,mode ='same'))
plt.ylabel("ANI")
plt.xlim((0,final_time))
# plt.ylim((0,0.002))
plt.legend(["Unfiltered","N=50 MA"])
plt.subplot(3,1,3)
Dfa_plot = waveform_tools.all_segements[waveform_tools.all_segements["DFA_a1"] != 0]

plt.plot(Dfa_plot["Time"],Dfa_plot["DFA_a1"],'o')
plt.plot(Dfa_plot["Time"],np.convolve(Dfa_plot["DFA_a1"],np.ones(N)/N,mode ='same'))
plt.ylabel("DFA_a1 ")
plt.legend(["Unfiltered","N=50 MA"])
plt.xlim((0,final_time))
plt.xlabel("Time s")


# querry.in_events_cv[querry.in_events_cv["HADM_ID"] == stay_id].to_csv("test4.csv",index=False)