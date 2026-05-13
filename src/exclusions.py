import pandas as pd
import pandasql as pds
import numpy as np
import warnings
from record import Record
from queries import MIMICQuery
from loadingBar import loading_bar
from datetime import datetime

class Exclusions:
    """
    A class for filtering and processing patient stay data from the MIMIC-III database.

    This class provides methods to filter patients based on ventilation and propofol administration,
    as well as to match waveform data with patient stays.

    Attributes:
        Querrys (MIMICQuery): An instance of the MIMICQuery class for querying the MIMIC database.
    """

    def __init__(self):
        """
        Initializes the Exclusions class and creates an instance of MIMICQuery.
        """
        self.Querrys = MIMICQuery()

    def filter_mv_patients(self, patients, print_length=True):
        """
        Filters patients to include only those with mechanical ventilation records.

        Args:
            patients (dict): A dictionary of patient data indexed by stay IDs.
            print_length (bool): Whether to print the length of the filtered subset.

        Returns:
            dict: A dictionary of patients with mechanical ventilation.
        """
        MV_subset = {}
        for stay in patients.keys():
            if self.Querrys.ventilation_query(stay):
                MV_subset[stay] = patients[stay]
        if print_length:
            print(f"\nN Propofol: {len(MV_subset)}")

        return MV_subset

    def filter_propofol_patients(self, patients, print_length=True):
        """
        Filters patients to include only those who received propofol.

        Args:
            patients (dict): A dictionary of patient data indexed by stay IDs.
            print_length (bool): Whether to print the length of the filtered subset.

        Returns:
            dict: A dictionary of patients who received propofol.
        """
        propofol_subset = {}
        total = len(patients)
        count = 0
        for stay in patients.keys():
            propdata = self.Querrys.propofol_query(stay)

            if propdata["IsPropfol"]:
                propofol_subset[stay] = patients[stay]

            count += 1
            if count % 10 == 0:
                loading_bar(total, count, "Extracting Propofol Patients:")

        if print_length:
            print(f"\nN MV: {len(propofol_subset)}")

        return propofol_subset

    def filter_med_patients(self, patients, print_length=True):
        """
        Filters patients to include only those in the MICU.

        Args:
            patients (dict): A dictionary of patient data indexed by stay IDs.
            print_length (bool): Whether to print the length of the filtered subset.

        Returns:
            dict: A dictionary of patients in the MICU.
        """
        med_subset = {}
        for stay in patients.keys():
            if patients[stay].care_unit == "MICU" or patients[stay].final_care_unit == "MICU":
                med_subset[stay] = patients[stay]
        if print_length:
            print(f"\nN MICU: {len(med_subset)}")

        return med_subset

    def remove_non_matching_stays(self, stay_data, waveform_date):
        """
        Removes stays from the stay_data DataFrame that do not match the given waveform date.

        Args:
            stay_data (pd.DataFrame): DataFrame containing patient stay data with a column 'INTIME' for the stay start date.
            waveform_date (datetime): The date to compare against.

        Returns:
            pd.DataFrame: A filtered DataFrame containing only stays that match the waveform date.
        """
        matching_stays = []
        for ii in range(len(stay_data)):
            # Convert the stay date from the DataFrame to a datetime object
            try:
                stay_date = datetime.strptime(stay_data.iloc[ii]["INTIME"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Handle cases where the date may be reformatted
                stay_date = datetime.strptime(stay_data.iloc[ii]["INTIME"], "%Y/%m/%d %H:%M:%S")

            # Compare the dates and retain matching stays
            if abs(stay_date - waveform_date).days <= 14:
                matching_stays.append(stay_data.iloc[ii])

        # Create a new DataFrame with matching stays
        filtered_stay_data = pd.DataFrame(matching_stays)

        if len(filtered_stay_data) > 1:
            warnings.warn(f"{stay_data.iloc[0]['SUBJECT_ID']}: Multiple Stays identified, removing Patient Record", UserWarning)
            filtered_stay_data = pd.DataFrame([])

        return filtered_stay_data

    def match_waveforms(self, waveforms):
        """
        Matches waveform data to patient stays.

        Args:
            waveforms (DataFrame): DataFrame containing waveform data.

        Returns:
            dict: A dictionary mapping valid stay IDs to their corresponding records.
        """
        valid_stayids = {}
        total = len(waveforms)
        count = 1
        previd = 0

        for waveform in waveforms.values:
            record_id = waveform[0][5:11]
            date = datetime.fromisoformat(waveform[0][20:30])

            if previd != record_id:
                stay_data = self.Querrys.stayid_query(int(record_id))
            previd = record_id

            stay_data_matched = self.remove_non_matching_stays(stay_data, date)
            if len(stay_data_matched) >= 1:
                stay_id = stay_data_matched["HADM_ID"].values[0]
                if stay_id not in valid_stayids:
                    valid_stayids[stay_id] = Record(stay_data_matched)
                    valid_stayids[stay_id].append_record(waveform)
                else:
                    valid_stayids[stay_id].append_record(waveform)

            count += 1
            if count % 10 == 0:
                loading_bar(total, count, "Grouping Records by Stay:")

        return valid_stayids
