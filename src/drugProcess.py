import pandas as pd
import datetime
import numpy as np
import warnings

# Define the Item IDs of sedatives and analgesics from MIMIC III.
# These IDs correspond to specific drug entries in the dataset.
sedatives_lookup = {"Propofol": [222168, 227210, 6238, 30131]}  # Item IDs for Propofol
analgesics_lookup = {"Fentanyl": [1], "RemiFentanyl": [1]}       # Item IDs for Fentanyl and Remifentanil

class DrugData:
    """
    This class handles the extraction and processing of ICU patient drug data,
    specifically focusing on sedatives and analgesics. It supports extracting
    the drug administration rates over time and prepares the data for
    pharmacokinetic (PK) modeling.
    
    Attributes:
        drug_data (pd.DataFrame): Patient's drug chart containing drug administration data.
        age (float): Patient's age.
        gender (str): Patient's gender.
        weight (float): Patient's weight.
        record (Record): Patient's entire medical record (currently unused but stored for potential future use).
        start_time (datetime): The start time of the drug administration window.
    """
    
    def __init__(self, patient_record, start_time) -> None:
        """
        Initializes the DrugData class with the patient's record and the drug administration start time.
        Verifies the availability of patient demographics and validates the start_time format.
        
        Args:
            patient_record (Record): An object that contains the patient's medical record, including drug chart.
            start_time (datetime): The time at which the drug administration began.

        Raises:
            TypeError: If start_time is not a valid datetime object.
        """
        self.drug_data = patient_record.drugChart  # Extract the drug chart from the patient record.
        self.age = patient_record.age              # Store the patient's age.
        self.gender = patient_record.gender        # Store the patient's gender.
        self.weight = patient_record.weight        # Store the patient's weight.

        # Check if all necessary demographic information is available.
        self._check_demographics()

        # Save the full patient record (currently unused but available if needed).
        self.record = patient_record

        # Store the start time of the drug administration period.
        self.start_time = start_time

        # Ensure that start_time is a datetime object.
        if not isinstance(self.start_time, datetime.datetime):
            raise TypeError(f"Expected a datetime object, but got {type(start_time).__name__} instead.")

    def _check_demographics(self):
        """
        Private method to check if demographic data (age, weight, gender) are available.
        If any key demographic data is missing, a warning is raised, and the PK models
        will not be applicable.
        """
        if self.age is None or self.weight is None or self.gender is None:
            # Warn if any demographic data is missing.
            warnings.warn("Demographics not found in record, PK models unavailable", UserWarning)
            self._demographics_available = False  # Flag that demographics are not available.
        else:
            self._demographics_available = True   # Flag that demographics are available.

    def _extract_drug_MV(self, drug, lookup_dict):
        """
        Private method to extract the time and rate data for a specified drug.

        This function uses the drug chart data to generate a timeline of drug
        administration and corresponding rate of administration. It works for both
        bolus doses and continuous infusions.

        Args:
            drug (str): The name of the drug to extract (e.g., "Propofol", "Fentanyl").
            lookup_dict (dict): Dictionary mapping drug names to their respective ITEMID codes.

        Returns:
            dict: A dictionary with two keys:
                - "Time": A numpy array of time points relative to the start_time.
                - "Rate": A numpy array of drug administration rates over time.
        """
        N = self.drug_data.shape[0]  # Number of records in the drug chart.
        # Parse the end time of the last drug administration event in the dataset.
        end_time = datetime.datetime.strptime(self.drug_data["ENDTIME"].iloc[-1], "%Y-%m-%d %H:%M:%S")
        T = end_time - self.start_time  # Total duration of the drug administration window.
        time_vec = np.arange(0, T.total_seconds(), 1)  # Generate a time vector (in seconds).
        rate_vec = np.zeros(len(time_vec))  # Initialize a rate vector with zeros.

        # Loop through each drug record and match it to the lookup table (based on ITEMID).
        for ii in range(N):
            if self.drug_data["ITEMID"].iloc[ii] in lookup_dict[drug]:
                # Get start and end times for each drug administration event.
                start_time = datetime.datetime.strptime(self.drug_data["STARTTIME"].iloc[ii], "%Y-%m-%d %H:%M:%S")
                t_start = (start_time - self.start_time).total_seconds()

                end_time = datetime.datetime.strptime(self.drug_data["ENDTIME"].iloc[ii], "%Y-%m-%d %H:%M:%S")
                t_end = (end_time - self.start_time).total_seconds()

                # Only process if the event starts after the recorded start_time.
                if t_start >= 0:
                    if pd.isna(self.drug_data["RATE"].iloc[ii]):
                        # If there is no rate provided, it's a bolus dose.
                        rate_vec[int(t_start):int(t_end) + 1] += self.drug_data["AMOUNT"].iloc[ii]
                    else:
                        # Otherwise, it is a continuous infusion with a specified rate.
                        rate_vec[int(t_start):int(t_end)] += self.drug_data["RATE"].iloc[ii]

        # Return the extracted time and rate vectors as a dictionary.
        return {"Time": time_vec, "Rate": rate_vec}

    def _extract_drug_CV3(self,drug,lookup_dict):
        N = self.drug_data.shape[0]  # Number of records in the drug chart.
        self.drug_data["CHARTTIME"] = pd.to_datetime(pd.to_datetime(self.drug_data["CHARTTIME"]))
        self.drug_data = self.drug_data.sort_values(by="CHARTTIME")
        end_time = self.drug_data["CHARTTIME"].iloc[-1]
        T = end_time - self.start_time  # Total duration of the drug administration window.
        # print(T)
        
        time_vec = np.arange(0, T.total_seconds(), 1)  # Generate a time vector (in seconds).
        rate_vec = np.zeros(len(time_vec))  # Initialize a rate vector with zeros.
        previous_time = None
        for ii in range(N):
            if self.drug_data["ITEMID"].iloc[ii] in lookup_dict[drug]:
                    if self.drug_data["ORIGINALROUTE"].iloc[ii] == "IV Drip":
                        chart_time = self.drug_data["CHARTTIME"].iloc[ii]
                        rate = self.drug_data["RATE"].iloc[ii]
                        t_end = (chart_time-self.start_time).total_seconds()
                        if previous_time is None:
                            t_start = t_end-(60*60)
                        else:
                            t_start = previous_time

                        previous_time = t_end

                        if t_start >= 0:
                            rate_vec[int(t_start):int(t_end)] += rate
                            # print(rate_vec)

        return {"Time": time_vec, "Rate": rate_vec}


    def _extract_drug_CV2(self,drug,lookup_dict):
        N = self.drug_data.shape[0]  # Number of records in the drug chart.

        self.drugdata = self.drug_data.sort_values(by="CHARTTIME")
        end_time = datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[-1], "%Y-%m-%d %H:%M:%S")
        T = end_time - self.start_time  # Total duration of the drug administration window.
        # print(T)
        
        time_vec = np.arange(0, T.total_seconds(), 1)  # Generate a time vector (in seconds).
        rate_vec = np.zeros(len(time_vec))  # Initialize a rate vector with zeros.
        previous_time = None
        for ii in range(N):
            # print(ii)
            if self.drug_data["ITEMID"].iloc[ii] in lookup_dict[drug]:
                if self.drug_data["ORIGINALROUTE"].iloc[ii] == "Intravenous Push":
                    chart_time = datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[ii], "%Y-%m-%d %H:%M:%S")
                    amount = self.drug_data["AMOUNT"].iloc[ii]
                    rate = amount /60
                    
                    t_end = (chart_time-self.start_time).total_seconds()
                    if previous_time is None:
                        t_start = t_end-(60*60)
                    else:
                        t_start = previous_time

                    previous_time = t_end

                    if t_start >= 0:
                        rate_vec[int(t_start):int(t_end)] += rate
                        print(rate_vec)
                    
        return {"Time": time_vec, "Rate": rate_vec}


    def _extract_drug_CV(self,drug,lookup_dict):
        N = self.drug_data.shape[0]  # Number of records in the drug chart.
       
        
        
        # if pd.isna(self.drug_data["RATE"].iloc[-1]):
        #     end_time = datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[-1], "%Y-%m-%d %H:%M:%S")
        # else:
        #     end_time = datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[-1], "%Y-%m-%d %H:%M:%S")

        # end_time = datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[1], "%Y-%m-%d %H:%M:%S")
        # for ii in range(N):
        #     newtime =datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[ii], "%Y-%m-%d %H:%M:%S")
        #     if (end_time-newtime).total_seconds()<=0:
        #         end_time =newtime
        # print(end_time)

        # T = end_time - self.start_time  # Total duration of the drug administration window.
        # print(T)
        
        # time_vec = np.arange(0, T.total_seconds(), 1)  # Generate a time vector (in seconds).
        # rate_vec = np.zeros(len(time_vec))  # Initialize a rate vector with zeros.

        # for ii in range(N):
        #     print(ii)
        #     if self.drug_data["ITEMID"].iloc[ii] in lookup_dict[drug]:
        #         if self.drug_data["ORIGINALROUTE"].iloc[ii] == "Intravenous Push":
        #             chart_time = datetime.datetime.strptime(self.drug_data["CHARTTIME"].iloc[ii], "%Y-%m-%d %H:%M:%S")
        #             amount = self.drug_data["AMOUNT"].iloc[ii]
        #             rate = amount /60
                    
        #             t_end = (chart_time-self.start_time).total_seconds()
        #             t_start = t_end-(60*60)
        #             if t_start >= 0:
        #                 rate_vec[int(t_start):int(t_end)] += rate
        #                 print(rate_vec)
                    
        # return {"Time": time_vec, "Rate": rate_vec}




    def extract_sedative(self, drug="Propofol",datatype= "CV"):
        """
        Public method to extract sedative data (by default, Propofol).
        It uses the _extract_drug method to retrieve the time and rate of the sedative administration.

        Args:
            drug (str): The sedative to extract (default is "Propofol").

        Returns:
            dict: A dictionary containing the time and rate vectors for the sedative.

        """

        if datatype =="CV":
            return self._extract_drug_CV3(drug, sedatives_lookup)
        elif datatype == "MV":
            return self._extract_drug_MV(drug, sedatives_lookup)
        
    def extract_analgesic(self, drug="Fentanyl"):
        """
        Public method to extract analgesic data (by default, Fentanyl).
        It uses the _extract_drug method to retrieve the time and rate of the analgesic administration.

        Args:
            drug (str): The analgesic to extract (default is "Fentanyl").

        Returns:
            dict: A dictionary containing the time and rate vectors for the analgesic.
        """
        return self._extract_drug(drug, analgesics_lookup)

    def get_analgesics_records(self):
        """
        Placeholder for a method to retrieve detailed analgesics records.
        This can be used to query the dataset for specific drug events.
        """
        pass

    def get_sedative_records(self):
        """
        Placeholder for a method to retrieve detailed sedative records.
        This can be used to query the dataset for specific sedative events.
        """
        pass

    def compute_Marsh_PK(self):
        """
        Placeholder for implementing the Marsh pharmacokinetics (PK) model for Propofol.
        This will calculate drug concentration based on patient data.
        """
        pass

    def compute_Minto_PK(self):
        """
        Placeholder for implementing the Minto pharmacokinetics (PK) model for Remifentanil.
        This will calculate drug concentration based on patient data.
        """
        pass

    def compute_Shafer_PK(self):
        """
        Placeholder for implementing the Shafer pharmacokinetics (PK) model for Fentanyl.
        This will calculate drug concentration based on patient data.
        """
        pass
