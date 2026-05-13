import pandas as pd
import pandasql as pds
import numpy as np
import warnings

class MIMICQuery:
    """
    A class to query MIMIC-III clinical database related to ICU stays and medication events.

    Attributes:
        patients (DataFrame): DataFrame containing patient information.
        cpt_events (DataFrame): DataFrame containing CPT event information.
        stays (DataFrame): DataFrame containing ICU stay information.
        in_events_cv (DataFrame): DataFrame containing continuous ventilation events.
        in_events_mv (DataFrame): DataFrame containing mechanical ventilation events.
        stay_dict (dict): Dictionary mapping subject IDs to their respective stay records.
        MV_dict (dict): Dictionary mapping hospital admission IDs to their respective MV records.
    """

    def __init__(self, min_los=5, max_los=14,import_filt_chart = False, filt_chart_file = "FILT_CHART_EVENTS.csv"):
        """
        Initializes the MIMICQuery class and loads necessary data.

        Args:
            min_los (int): Minimum length of stay to filter the stays. Default is 5 days.
            max_los (int): Maximum length of stay to filter the stays. Default is 14 days.
        """
        self.patients = pd.read_csv("M3_Clincial/PATIENTS.csv")
        self.cpt_events = pd.read_csv("M3_Clincial/CPTEVENTS.csv")
        self.stays = pd.read_csv("M3_Clincial/ICUSTAYS.csv")
        self.in_events_cv = pd.read_csv("M3_Clincial/INPUTEVENTS_CV.csv")
        self.in_events_mv = pd.read_csv("M3_Clincial/INPUTEVENTS_MV.csv")

        if import_filt_chart:
            try:
                self.chart_events = pd.read_csv(filt_chart_file)
            except FileNotFoundError:
                warnings.warn("No Filtered Chart File Found",UserWarning)
        self._stay_query(max_los, min_los)
        self._MV_query()
        self.sed_score_lookup = {228302:"CAM-ICU RASS LOC",228096:"Richmond-RAS Scale",223753:"Riker-SAS Scale"}
        self.sedation_scores = ["Riker-SAS Scale"]

    def _stay_query(self, max_los, min_los):
        """
        Private method to filter stays based on length of stay (LOS) and store results.

        Args:
            max_los (int): Maximum length of stay to filter the stays.
            min_los (int): Minimum length of stay to filter the stays.
        """
        if max_los is None or min_los is None:
            query = """
                    SELECT * 
                    FROM stays
                    """      
        else:
            query = f"""
                    SELECT * 
                    FROM stays
                    WHERE LOS >= {min_los}
                    AND LOS <= {max_los}  
                    """
        
        stays_filtered = pds.sqldf(query, {'stays': self.stays})
        stay_dict = {}
        
        # Group stays by SUBJECT_ID and store in a dictionary
        for subject_id, group in stays_filtered.groupby('SUBJECT_ID'):
            stay_dict[subject_id] = group

        self.stay_dict = stay_dict

    def _MV_query(self):
        """
        Private method to query mechanical ventilation (MV) events and store results.
        """
        query = """
        SELECT * 
        FROM cpt_events
        WHERE COSTCENTER = 'Resp'
        AND DESCRIPTION = 'VENT MGMT;SUBSQ DAYS(INVASIVE)'
        """
        
        MV_stays = pds.sqldf(query, {'cpt_events': self.cpt_events})
        MV_dict = {}
        
        # Group MV stays by HADM_ID and store in a dictionary
        for hadm_id, group in MV_stays.groupby('HADM_ID'):
            MV_dict[hadm_id] = group

        self.MV_dict = MV_dict

    def stayid_query(self, subject_id):
        """
        Queries the stay information for a specific subject ID.

        Args:
            subject_id (int): The ID of the subject to query.

        Returns:
            DataFrame: The stay information for the specified subject ID, or an empty DataFrame if not found.
        """
        if subject_id in self.stay_dict:
            return self.stay_dict[subject_id]
        else:
            return pd.DataFrame([])

    def ventilation_query(self, stay_id):
        """
        Checks if a specific stay ID has mechanical ventilation records.

        Args:
            stay_id (int): The hospital admission ID to check.

        Returns:
            bool: True if the stay ID has ventilation records, otherwise False.
        """
        return stay_id in self.MV_dict

    def propofol_query(self, stay_id):
        """
        Queries propofol administration data for a specific stay ID.

        Args:
            stay_id (int): The hospital admission ID to query.

        Returns:
            dict: A dictionary containing information about propofol administration, including:
                - IsPropfol (bool): Whether propofol was administered.
                - datatype (str or None): Type of data ("MV" for metavision or "CV" for careview) or None.
                - data (DataFrame): DataFrame containing the propofol administration records, or an empty DataFrame.
        """
        mv_data = self.in_events_mv[self.in_events_mv["HADM_ID"] == stay_id]
        mv_prop = mv_data[(mv_data["ITEMID"].values == 222168) | (mv_data["ITEMID"].values == 227210)]

        cv_data = self.in_events_cv[self.in_events_cv["HADM_ID"] == stay_id]
        cv_prop = cv_data[(cv_data["ITEMID"].values == 6238) | (cv_data["ITEMID"].values == 30131)]

        if len(mv_prop) == 0 and len(cv_prop) == 0:
            return {"IsPropfol": False, "datatype": None, "data": pd.DataFrame([])}
        elif len(mv_prop) != 0 and len(cv_prop) == 0:
            return {"IsPropfol": True, "datatype": "MV", "data": mv_prop}
        elif len(mv_prop) == 0 and len(cv_prop) != 0:
            return {"IsPropfol": True, "datatype": "CV", "data": cv_prop}
        else:
            warnings.warn("Found Data in MV and CV records, abandoned patient", UserWarning)
            return {"IsPropfol": False, "datatype": None, "data": pd.DataFrame([])}

    def analgesic_querries(self,stay_id):
        fentanyl_codes = [5464,1342,1355,1361,1412,3432,5261,2672,5077,6352,30150,30308,30118,301149,43387,221774,225972,225942]
        morphine_codes =[1813,30153,30126,225154]
        analgesic_codes = fentanyl_codes + morphine_codes

        mv_data = self.in_events_mv[self.in_events_mv["HADM_ID"] == stay_id]
        mv_analg = mv_data[mv_data["ITEMID"].values in analgesic_codes]

        cv_data = self.in_events_cv[self.in_events_mv["HADM_ID"] == stay_id]
        cv_analg = np.where(np.isin(cv_data["ITEMID"].values, analgesic_codes))

        if len(mv_analg) == 0 and len(cv_analg) == 0:
            return {"IsPropfol": False, "datatype": None, "data": pd.DataFrame([])}
        elif len(mv_analg) != 0 and len(cv_analg) == 0:
            return {"IsPropfol": True, "datatype": "MV", "data": mv_analg}
        elif len(mv_analg) == 0 and len(cv_analg) != 0:
            return {"IsPropfol": True, "datatype": "CV", "data": cv_analg}
        else:
            warnings.warn("Found Data in MV and CV records, abandoned patient", UserWarning)
            return {"IsPropfol": False, "datatype": None, "data": pd.DataFrame([])}
        
    def sed_score_querry(self,stay_id):
        patient_chart = self.chart_events[self.chart_events["HADM_ID"]==stay_id]
        PS_scores = patient_chart[patient_chart["ITEMID"].isin(self.sed_score_lookup.keys())]

        return PS_scores


    def get_patient_sedation_counts(self,stay_ids):

        score_count = {"Stay_id":[], "Score_Count":[]}
        for id in stay_ids:
            scores = self.sed_score_querry(id)
            N = len(scores)
            score_count["Stay_id"].append(id)
            score_count["Score_Count"].append(N)

        return pd.DataFrame(score_count)
    
    def get_sedative_dose_count(self,stay_ids):
        dose_count = {"Stay_id":[], "Dose_Count":[]}

        for id in stay_ids:
            doses = self.propofol_query(id)
            N= len(doses["data"])
            dose_count["Stay_id"].append(id)
            dose_count["Dose_Count"].append(N)

        return pd.DataFrame(dose_count)