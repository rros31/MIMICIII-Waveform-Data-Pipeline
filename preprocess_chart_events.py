#13/11/24 Ryan O'Sullivan

#In MIMIC III Chart data is too large to import into python for querries. 
# This script will import a records variable as a PKL file and extract the relevant patients chart data into a subtable. 
# This File can be imported by querry class.



import pickle

import dask as dd 
from drugProcess import DrugData
from datetime import datetime
from queries import MIMICQuery
import pandas as pd

def extract_patient_charts(records_file,results_file):

    with open(records_file, 'rb') as file: 
        records = pickle.load(file)


    stay_ids = list(records.keys())
    # df = dd.read_csv('M3_Clincial/CHARTEVENTS.csv')


    # chart  = df[df["HADM_ID"]==stay_ids].compute()

    # print(chart)
    chunksize = 1000000
    count=0
    QuerryRes = pd.DataFrame([])
    for chunk in pd.read_csv('M3_Clincial/CHARTEVENTS.csv', chunksize=chunksize):
        print(count)
        count+=1
        QuerryRes = pd.concat([QuerryRes, chunk[chunk["HADM_ID"].isin(stay_ids)]],ignore_index=True)

    QuerryRes.to_csv(results_file,index=False)

if __name__ == "__main__":
    extract_patient_charts('sedated_subset.pkl','FILT_CHART_EVENTS.csv')