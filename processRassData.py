import pandas as pd
import numpy as np
import pickle
from queries import MIMICQuery
from datetime import datetime 
from drugProcess import DrugData
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
%matplotlib qt
def transform_riker(sed_times,sed_num_score):
    df = pd.DataFrame({
    'Time': sed_times,
    'SedationScore': sed_num_score
    })
    df_sorted = df.sort_values(by='Time', ascending=True)
    df_sorted["SedTransform"] = df_sorted["SedationScore"]*100/6-1
    return df_sorted

def transform_richmond(sed_times,sed_num_score):
    df = pd.DataFrame({
    'Time': sed_times,
    'SedationScore': sed_num_score
    })
    df_sorted = df.sort_values(by='Time', ascending=True)
    df_sorted["SedTransform"] = df_sorted["SedationScore"]*100/9+55.6
    return df_sorted
ids = pd.read_csv("N21Rassscores.csv")

stay_ids = ids.values

with open('sedated_subset.pkl', 'rb') as file: 
    records = pickle.load(file)

querry = MIMICQuery(import_filt_chart=True,filt_chart_file="FILT_CHART_EVENTS2.csv")

for id in stay_ids:
    sedscore = querry.sed_score_querry(id[0])
    sedtype = querry.sed_score_lookup[sedscore["ITEMID"].iloc[0]]
    print(sedtype)
    propQuerry = querry.propofol_query(id[0])
    records[id[0]].drugChart= propQuerry["data"]


    start_time = records[id[0]].start_date
    sed_times = []
    sed_num_score = []

    for ii in range(len(sedscore)):
        sed_times.append((datetime.strptime(sedscore["CHARTTIME"].iloc[ ii], "%Y-%m-%d %H:%M:%S") -start_time).total_seconds())
        sed_num_score.append(sedscore["VALUENUM"].iloc[ii])

    sedtype = querry.sed_score_lookup[sedscore["ITEMID"].iloc[0]]


    if sedtype == 'Richmond-RAS Scale':
        sed_scores = transform_richmond(sed_times,sed_num_score)
    else: #fix this
        sed_scores = transform_riker(sed_times,sed_num_score)

    
    drug_data = DrugData(records[id[0]],start_time)
    sedative = drug_data.extract_sedative(datatype=propQuerry["datatype"])
    cs = CubicSpline(sed_scores["Time"],sed_scores["SedTransform"])  
    
    plt.figure()
    plt.subplot(2,1,1)
    plt.plot(sedative["Time"],cs(sedative["Time"]))
    plt.plot(sed_scores["Time"],sed_scores["SedTransform"],'o')
    plt.subplot(2,1,2)
    plt.plot(sedative["Time"],sedative["Rate"])
