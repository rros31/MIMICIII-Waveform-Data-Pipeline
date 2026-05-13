
from json import load
import pandas as pd
import pandasql as pds
import numpy as np
from datetime import datetime
import os

from record import Record
import warnings
import requests
from bs4 import BeautifulSoup
import sys
import pickle
import wget
# prescriptions = pd.read_csv("M3_Clincial/PRESCRIPTIONS.csv")
patients = pd.read_csv("M3_Clincial/PATIENTS.csv")
cpt_events= pd.read_csv("M3_Clincial/CPTEVENTS.csv")
stays = pd.read_csv("M3_Clincial/ICUSTAYS.csv")
in_events_cv = pd.read_csv("M3_Clincial/INPUTEVENTS_CV.csv")
in_events_mv = pd.read_csv("M3_Clincial/INPUTEVENTS_MV.csv")
# Load all stays where LOS > 5

query = """
    SELECT * 
    FROM stays
    WHERE LOS >= 5
    AND LOS<=14
"""

stays_filtered = pds.sqldf(query, {'stays': stays})
stay_dict = {}
for subject_id, group in stays_filtered.groupby('SUBJECT_ID'):
    stay_dict[subject_id] = group


query = """
    SELECT * 
    FROM cpt_events
    WHERE COSTCENTER = 'Resp'
    AND DESCRIPTION = 'VENT MGMT;SUBSQ DAYS(INVASIVE)'
"""
MV_stays = pds.sqldf(query, {'cpt_events': cpt_events})

MV_dict = {}
for hadm_id, group in MV_stays.groupby('HADM_ID'):
    MV_dict[hadm_id] = group


# query = """
# SELECT * 
# FROM input_events
# WHERE ITEMID = 222168
# OR ITEMID = 227210
# """
# mv_prop = pds.sqldf(query, {'input_events': in_events_mv})

# query = """
# SELECT * 
# FROM input_events
# WHERE ITEMID = 6238
# OR ITEMID = 30131
# """
# cv_prop = pds.sqldf(query, {'input_events': in_events_cv})
# # MV_dict = {}
# # for hadm_id, group in stays_filtered.groupby('HADM_ID'):
# #     MV_dict[hadm_id] = group


def loading_bar(total_records, current_record,message):
    """
    Displays a loading bar in the terminal.

    Parameters:
    total_records (int): Total number of records to process.
    current_record (int): The current record being processed.
    """
    # Calculate the percentage of completion
    percentage = (current_record / total_records) * 100
    bar_length = 40  # Length of the loading bar
    block = int(round(bar_length * percentage / 100))  # Calculate the number of blocks to show

    # Create the loading bar string
    bar = "#" * block + "-" * (bar_length - block)
    
    # Print the loading bar with the percentage
    sys.stdout.write(f"\r{message}|{bar}| {percentage:.2f}%")
    sys.stdout.flush()  # Flush the output buffer

def stayid_querry(subject_id):
    if subject_id in stay_dict:
        return stay_dict[subject_id]
    else:
        return pd.DataFrame([])

def ventilationQuery(stay_id):
    if stay_id in MV_dict:
        return True
    else:
        return False

def propofolQuerry(stay_id):
    mv_data = in_events_mv[in_events_mv["HADM_ID"]== stay_id]
    mv_prop = mv_data[(mv_data["ITEMID"].values==222168) | (mv_data["ITEMID"].values==227210)]
    
    cv_data = in_events_cv[in_events_cv["HADM_ID"]== stay_id]
    cv_prop = cv_data[(cv_data["ITEMID"].values==6238) | (cv_data["ITEMID"].values==30131)]

    if len(mv_prop) ==0 and len(cv_prop)==0:
        return {"IsPropfol":False,"datatype":None,"data":pd.DataFrame([])}
    elif len(mv_prop) !=0 and len(cv_prop)==0:
        return {"IsPropfol":True,"datatype":"MV","data":mv_prop}
    elif len(mv_prop) ==0 and len(cv_prop)!=0:
        return {"IsPropfol":True,"datatype":"CV","data":cv_prop}
    else:
        return {"IsPropfol":False,"datatype":None,"data":pd.DataFrame([])}
        warnings.warn("Found Data in MV and CV records, abonded patient",UserWarning)

def remove_non_matching_stays(stay_data, waveform_date):
    """
    Removes stays from the stay_data DataFrame that do not match the given waveform date.

    Parameters:
    -----------
    stay_data : pd.DataFrame
        DataFrame containing patient stay data with a column 'INTIME' for the stay start date.
    waveform_date : str
        The date string to compare against in the format 'YYYY-MM-DD HH:MM:SS'.

    Returns:
    --------
    pd.DataFrame:
        A filtered DataFrame containing only stays that match the waveform date.
    """

    matching_stays = []
    for ii in range(len(stay_data)):
        # Convert the stay date from the DataFrame to a datetime object
        try:
            stay_date = datetime.strptime(stay_data.iloc[ii]["INTIME"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            #If opened in Excel, Date may be reformatted.
            stay_date = datetime.strptime(stay_data.iloc[ii]["INTIME"], "%Y/%m/%d %H:%M:%S")

        # Compare the dates and retain matching stays
        if abs(stay_date - waveform_date).days <=14:
            matching_stays.append(stay_data.iloc[ii])
    
    # Create a new DataFrame with matching stays
    filtered_stay_data = pd.DataFrame(matching_stays)
    
    if len(filtered_stay_data)>1:
        # warnings.warn(f"{stay_data.iloc[0]["SUBJECT_ID"]}: Mutiple Stays identfied, Removing Patient Record",UserWarning)
        filtered_stay_data = pd.DataFrame([])

    return filtered_stay_data

def match_waveforms(waveforms):

    valid_stayids = {}
    #Match waveform to stayid

    total = len(waveforms)
    count =1
    previd=0
    for waveform in waveforms.values:
        record_id = waveform[0][5:11]
        date = datetime.fromisoformat(waveform[0][20:30])

        if previd != record_id:
            stay_data = stayid_querry(int(record_id))
        previd = record_id

        
        
        stay_data_matched = remove_non_matching_stays(stay_data, date)
        if len(stay_data_matched)>=1:
            stay_id = stay_data_matched["HADM_ID"].values[0] 
            if stay_id not in valid_stayids:
                valid_stayids[stay_id] = Record(stay_data_matched)
                valid_stayids[stay_id].append_record(waveform)
            else:
                valid_stayids[stay_id].append_record(waveform)
            
            # print(count)
        count +=1
        if count%10==0:
            loading_bar(total,count,"Grouping Records by Stay:")

    return valid_stayids

def download_patient_data(subject_ids):
    # Get today's date in the format YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Create a directory for today's downloads
    download_dir = "waveforms"
    os.makedirs(download_dir, exist_ok=True)
    TotalP = len(subject_ids)
    countP = 1
    for subject_id in subject_ids:
        loading_bar(TotalP,countP,f"Patient {countP}/{TotalP}")
        countP +=1
        # Zero-pad the subject_id to ensure it is 6 digits
        padded_id = f"{subject_id:06d}"
        
        # Construct the URL to the subject's directory
        url = f"https://physionet.org/files/mimic3wdb-matched/1.0/p00/p{padded_id}/"
        
        # Create a subdirectory for the subject
        subject_download_dir = os.path.join(download_dir, padded_id)
        os.makedirs(subject_download_dir, exist_ok=True)

        # Fetch the directory contents
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check if the request was successful

            # Parse the HTML content to find file links
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')

            # Download each file found in the directory
            total = len(links)
            count = 0
            for link in links:
                loading_bar(total,count,f"Patient:{subject_id}:")
                count+=1
                file_name = link.get('href')
                if file_name and not file_name.endswith('/'):  # Skip directories
                    file_url = url + file_name
                    file_path = os.path.join(subject_download_dir, file_name)
                    # print(f"Downloading {file_url} to {file_path}")
                    # Download the file
                    wget.download(file_url, out=file_path)

            print(f"Downloaded data for subject ID: {padded_id}")
        
        except Exception as e:
            print(f"Failed to download data for subject ID {padded_id}: {e}")

def filter_mv_patients(patients,print_length=True):
    MV_subset = {}
    for stay in patients.keys():
        if ventilationQuery(stay):
            MV_subset[stay] = patients[stay]
    if print_length:
        print()
        print(f"N Propofol: {len(MV_subset)}")

    return MV_subset


def filter_propofol_patients(patients,print_length=True):
    propofol_subset = {}

    total =len(patients)
    count =0
    for stay in patients.keys():
        propdata = propofolQuerry(stay)

        if propdata["IsPropfol"]:
            propofol_subset[stay] = patients[stay]

        count +=1
        if count%10==0:
            loading_bar(total,count,"Extracting Propofol Patients:")

    if print_length:
        print()
        print(f"N MV: {len(propofol_subset)}")

    return propofol_subset


def filter_med_patietnts(patients, print_length=True):
    med_subset = {}
    for stay in patients.keys():
        if patients[stay].care_unit == "MICU" or patients[stay].final_care_unit == "MICU":
            med_subset[stay] =patients[stay]
    if print_length:
        print()
        print(f"N MICU: {len(med_subset)}")

    return med_subset

def main(downloadFiles=False, save_pickle = True):
    allrecords = pd.read_csv("RECORDS",header=None)
    waveforms = pd.read_csv("RECORDS-waveforms",header=None)

    valid_stay_ids = match_waveforms(waveforms)

    MV_subset = filter_mv_patients(valid_stay_ids)

    propofol_subset = filter_propofol_patients(MV_subset)

    med_subset= filter_med_patietnts(propofol_subset)
    if save_pickle:
        with open('sedated_subset.pkl', 'wb') as file: 
            # A new file will be created 
            pickle.dump(propofol_subset, file) 

        
    validids = []
    for stay in med_subset.keys():
        validids.append(med_subset[stay].id)

    if downloadFiles:
        download_patient_data(validids)


if __name__ == "__main__":
    main()


# query = """
# SELECT * 
# FROM clinicalPrescriptions
# WHERE subject_id = 000085;
# """

# result_df =pds.sqldf(query, locals())

