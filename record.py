from datetime import datetime
import warnings
import pandas as pd

class Record:
    """
    A class to represent a patient's stay record in the hospital.

    Attributes:
    -----------
    id : int
        A unique identifier for the patient.
    stayid : int
        A unique identifier for the patient's hospital stay.
    start_date : datetime
        The start date of the hospital stay (must be a datetime object).
    LOS : int
        The length of stay in days.
    age : int
        The age of the patient.
    care_unit : str
        The type of care unit (e.g., ICU, general ward) the patient was admitted to.
    gender : str
        The gender of the patient (e.g., Male, Female).
    records : list
        A list to store records related to this patient stay.

    Methods:
    --------
    __init__(self, id, stayid, start_date, LOS, age, care_unit, gender):
        Initializes the record with the required patient stay information.
        
    __str__(self):
        Returns a string representation of the Record object.

    _check_record(self, record):
        Private method to check if the record is valid and its date is within 30 days of the start date.

    append_record(self, record):
        Appends a new record to the `records` list and checks its validity.

    get_id(self):
        Returns the patient ID.

    get_start_date(self):
        Returns the start date of the hospital stay.

    get_LOS(self):
        Returns the length of stay in days.

    get_age(self):
        Returns the age of the patient.

    get_care_unit(self):
        Returns the care unit type of the stay.

    get_gender(self):
        Returns the gender of the patient.
    """

    def __init__(self, stayTable, gender = None, age = None, weight = None):
        """
        Initializes a Record instance with essential information about the patient's hospital stay.

        Parameters:
        -----------
        Patients MIMIC stay table, including:
            id : int
                Unique identifier for the patient.
            stayid : int
                Unique identifier for the patient's hospital stay.
            start_date : datetime
                The start date of the hospital stay.
            LOS : int
                Length of stay in days.
            
            care_unit : str
                The type of care unit (e.g., ICU).

        gender : str
            Gender of the patient (e.g., Male, Female).

        age : int
                Age of the patient.

        weight: int
                Weight of the patient
        Raises:
        -------
        ValueError:
            If start_date is not a datetime object.
        """
        self.id = stayTable["SUBJECT_ID"].values[0]
        self.stayid = stayTable["HADM_ID"].values[0]
        start_date = datetime.strptime(stayTable["INTIME"].values[0], "%Y-%m-%d %H:%M:%S")
        if not isinstance(start_date, datetime):
            raise ValueError("start_date must be a datetime object.")
        self.start_date = start_date  # Start date of the hospital stay
        self.LOS = stayTable["LOS"].values[0]  # Length of stay (in days)
        
        self.care_unit = stayTable["FIRST_CAREUNIT"].values[0] # Type of care unit (e.g., ICU, general ward)
        self.final_care_unit = stayTable["LAST_CAREUNIT"].values[0]
        #Variables not in stay table, that can be passed in now or later:

        self.gender = gender  # Gender of the patient (Male, Female)
        self.age = age  # Age of the patient
        self.weight = weight
        self.records = []  # List to store associated records for this patient stay
        self.drugChart = pd.DataFrame([])
    def __str__(self):
        """
        Returns a string representation of the Record instance, displaying patient details.

        Returns:
        --------
        str:
            A formatted string showing the patient ID, start date, length of stay, age, care unit, and gender.
        """
        return (f"Record(ID: {self.id},Hadm_id: {self.stayid},  Start Date: {self.start_date}, "
                f"LOS: {self.LOS}, Age: {self.age}, "
                f"Care Unit: {self.care_unit}, Gender: {self.gender})")

    def _check_record(self, record):
        """
        A private method that checks the validity of an appended record.

        Ensures that the record's date is within 30 days from the start date of the hospital stay.
        If the record's date is more than 30 days apart, it raises a warning.

        Parameters:
        -----------
        gender : str
            Gender of the patient (e.g., Male, Female).

        age : int
                Age of the patient.

        weight: int
                Weight of the patient
        Raises:
        -------
        UserWarning:
            If Value is already assinged to demographic instance.
        """
        if isinstance(record, (list, tuple)) and len(record) > 0:
            try:
                # Extracts date from the record (assuming record[0] contains ISO formatted date string)
                date = datetime.fromisoformat(record[0][20:30])
                time_diff = abs((date - self.start_date).days)
                if time_diff > 30:
                    warnings.warn("Appended Record is greater than 30 days from the start of stay", UserWarning)
            except (ValueError, IndexError) as e:
                warnings.warn(f"Invalid record format: {e}", UserWarning)

    def set_patient_demographics(self, gender = None, age = None, weight = None):
        """
        Will assing the passed in demographics to the record, Will only assign where type is not none and will warn if overiding previous value

        Parameters:
        -----------
        record : list or tuple
            The record to be appended. This should ideally contain a date as the first element.

        Calls:
        ------
        _check_record(record):
            A private method to check the validity of the record's date.
        """
        #Redudant logic for readability (Maybe)
        if (self.gender is None) and (gender is not None):
            self.gender = gender  # Gender of the patient (Male, Female)
        elif (self.gender is not None) and (gender is not None):
            self.gender = gender
            warnings.warn("Sex Already Assinged (Overwritten)",UserWarning)

        if (self.age is None) and (age is not None):
            self.age= age  
        elif (self.age is not None) and (age is not None):
            self.age = age
            warnings.warn("Age Already Assinged (Overwritten)",UserWarning)

        if (self.weight is None) and (weight is not None):
            self.weight= weight  
        elif (self.weight is not None) and (weight is not None):
            self.weight= weight
            warnings.warn("Weight Already Assinged (Overwritten)",UserWarning)
        

    def append_record(self, record):
        """
        Appends a record to the `records` list and validates it.

        Parameters:
        -----------
        record : list or tuple
            The record to be appended. This should ideally contain a date as the first element.

        Calls:
        ------
        _check_record(record):
            A private method to check the validity of the record's date.
        """
        self.records.append(record)
        self._check_record(record)  # Check the record's validity

    # Getter methods for encapsulation of attributes
    def get_id(self):
        """Returns the patient's unique identifier (ID)."""
        return self.id

    def get_start_date(self):
        """Returns the start date of the hospital stay."""
        return self.start_date

    def get_LOS(self):
        """Returns the length of stay (LOS) in days."""
        return self.LOS

    def get_age(self):
        """Returns the patient's age."""
        return self.age

    def get_care_unit(self):
        """Returns the care unit type (e.g., ICU, general ward)."""
        return self.care_unit

    def get_gender(self):
        """Returns the patient's gender (e.g., Male, Female)."""
        return self.gender
