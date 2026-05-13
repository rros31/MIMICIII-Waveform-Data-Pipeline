from queries import MIMICQuery

from drugProcess import DrugData
from patient_review_gui import PatientReviewGUI
import numpy as np
import matplotlib.pyplot as plt
import pickle
from datetime import datetime
import pandas as pd
import tkinter as tk
from loadingBar import loading_bar
with open('sedated_subset.pkl', 'rb') as file: 
    records = pickle.load(file)

querry = MIMICQuery(import_filt_chart=True,filt_chart_file="FILT_CHART_EVENTS2.csv")


stay_ids = list(records.keys())
sed_count = querry.get_patient_sedation_counts(stay_ids)

dose_count = querry.get_sedative_dose_count(stay_ids)

merged_df = sed_count.merge(dose_count, on="Stay_id", how="outer", suffixes=('_sed', '_dose'))

merged_df['Total_Count'] = merged_df['Score_Count'] + merged_df['Dose_Count']

merged_df['Mult_Count'] = merged_df['Score_Count']* merged_df['Dose_Count']

ordered = merged_df.sort_values(by="Mult_Count", ascending=False)

stay_ids = ordered["Stay_id"]

count =1

allsedtimes=[]
allsednums=[]
allproptimes=[]
allpropnums=[]
checked_ids = []
for id in stay_ids:
    #Sed scores
    loading_bar(len(stay_ids), count, f"Patient {count}/{len(stay_ids)}")
    count +=1
    sedscore = querry.sed_score_querry(id)

    propQuerry = querry.propofol_query(id)
    records[id].drugChart= propQuerry["data"]


    start_time = records[id].start_date
    sed_times = []
    sed_num_score = []

    for ii in range(len(sedscore)):
        sed_times.append((datetime.strptime(sedscore["CHARTTIME"].iloc[ ii], "%Y-%m-%d %H:%M:%S") -start_time).total_seconds())
        sed_num_score.append(sedscore["VALUENUM"].iloc[ii])


    
    drug_data = DrugData(records[id],start_time)
    sedative = drug_data.extract_sedative(datatype=propQuerry["datatype"])


    allsedtimes.append(sed_times)
    allsednums.append(sed_num_score)
    allproptimes.append(sedative["Time"])
    allpropnums.append(sedative["Rate"])
    checked_ids.append(id)
    if len(sed_num_score)==0:
        break
    # Sample data for demonstration



data = pd.DataFrame({
    'id': checked_ids,
    'time_Sed':  allsedtimes,
    'Sed': allsednums,
    'time_propofol': allproptimes,
    'propofol': allpropnums
})

# Define the variables you want to plot
plot_vars = ["Sed", "propofol"]
plot_syms = ['o','-']

# Initialize the GUI
root = tk.Tk()
app = PatientReviewGUI(root, data, plot_vars,plot_syms)
root.mainloop()

# Save accepted IDs if needed
print("Accepted Patient IDs:", app.accepted_ids)
