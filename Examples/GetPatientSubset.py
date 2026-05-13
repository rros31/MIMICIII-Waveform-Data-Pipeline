import os
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from loadingBar import loading_bar
from record import Record
from exclusions import Exclusions
import wget
import pickle
def download_patient_data(subject_ids):
    """
    Downloads patient waveform data from the PhysioNet MIMIC-III database.

    Args:
        subject_ids (list): A list of subject IDs to download data for.
    """
    # Get today's date in the format YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Create a directory for today's downloads
    download_dir = "waveforms"
    os.makedirs(download_dir, exist_ok=True)

    TotalP = len(subject_ids)
    countP = 1
    for subject_id in subject_ids:
        loading_bar(TotalP, countP, f"Patient {countP}/{TotalP}")
        countP += 1

        # Zero-pad the subject_id to ensure it is 6 digits
        padded_id = f"{subject_id:06d}"
        subid = padded_id[0:2]
        # Construct the URL to the subject's directory
        url = f"https://physionet.org/files/mimic3wdb-matched/1.0/p{subid}/p{padded_id}/"

        folders = [f for f in os.listdir(download_dir) if os.path.isdir(os.path.join(download_dir, f))]
        # Create a subdirectory for the subject

        if padded_id in folders:
            print(f" Patient {padded_id}: Data already Downloaded")
    
        else:
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
                    loading_bar(total, count, f"Patient: {subject_id} ({countP}/{TotalP}):")
                    count += 1
                    file_name = link.get('href')
                    if file_name and not file_name.endswith('/'):  # Skip directories
                        file_url = url + file_name
                        file_path = os.path.join(subject_download_dir, file_name)
                        # Download the file
                        wget.download(file_url, out=file_path)

                print(f"Downloaded data for subject ID: {padded_id}")
            
            except Exception as e:
                print(f"Failed to download data for subject ID {padded_id}: {e}")
                os.rmdir(subject_download_dir, exist_ok=True)
def main(downloadFiles=True):
    """
    Main function to filter patient data and download the relevant waveform data.

    Args:
        downloadFiles (bool): A flag to determine whether to download files.

    -------------------------------------------------------------------------------------
    NOTE: Downloading MIMIC waveform is EXTREMELY SLOW, Likely on PHYSIO NETS END
          Any ideas to improve this appeciated!
    -------------------------------------------------------------------------------------
    """
    # Load records and waveforms from CSV files
    allrecords = pd.read_csv("RECORDS", header=None)
    waveforms = pd.read_csv("RECORDS-waveforms", header=None)

    exclusions = Exclusions()

    # Match waveforms to valid stay IDs
    valid_stay_ids = exclusions.match_waveforms(waveforms)

    # Filter patients based on ventilation and propofol usage
    MV_subset = exclusions.filter_mv_patients(valid_stay_ids)

    propofol_subset = exclusions.filter_propofol_patients(MV_subset)

    med_subset = exclusions.filter_med_patients(propofol_subset)

    # Gather valid IDs for downloading
    validids = [med_subset[stay].id for stay in med_subset.keys()]

    #Save Patient Records:
    #Save Patient Records:
    with open("Patient_Subset.pkl", "wb") as f:
        pickle.dump(med_subset, f)

    if downloadFiles:
        download_patient_data(validids)

if __name__ == "__main__":
    main()

