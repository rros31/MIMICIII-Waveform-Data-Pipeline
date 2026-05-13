# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 10:10:19 2022

@author: cca78
"""

import numpy as np
import pandas as pd

class results:
    def __init__(self):
        self.columns = ["Consult Room",
                        "On Table",
                        "Initial Insertion",
                        "Max. Insertion",
                        "Scope Removed",
                        "End Procedure",
                        "Abnormal Procedure End",
                        "Wait for Procedure",
                        "Vasovagal",
                        "Bend",
                        "Polyp Removal",
                        "Pressure Applied"]

        rmssd_df = pd.DataFrame([], columns=self.columns)
        sdnn_df = pd.DataFrame([], columns=self.columns)
        pnn50_df = pd.DataFrame([], columns=self.columns)
        VLF_df = pd.DataFrame([], columns=self.columns)
        LF_df = pd.DataFrame([], columns=self.columns)
        HF_df = pd.DataFrame([], columns=self.columns)
        LF_HF_df = pd.DataFrame([], columns=self.columns)
        AC_df = pd.DataFrame([], columns=self.columns)
        DC_df = pd.DataFrame([], columns=self.columns)
        AC_DC_df = pd.DataFrame([], columns=self.columns)
        DFA_a1_df = pd.DataFrame([], columns=self.columns)
        duration_df = pd.DataFrame([], columns=self.columns)
        num_beats_df = pd.DataFrame([], columns=self.columns)
        BSI_df = pd.DataFrame([], columns=self.columns)
        TINN_df = pd.DataFrame([], columns=self.columns)
        HRVi_df = pd.DataFrame([], columns=self.columns)
        self.savepath = "//file/Usersc$/cca78/Home/My Documents/Work/Research Projects/R-R/Analysis/RR_data/processed_results/results.xlsx"


        self.dataframes = {"rmssd":  rmssd_df,
                           "sdnn":   sdnn_df,
                           "pnn50":  pnn50_df,
                           "VLF":    VLF_df,
                           "LF":     LF_df,
                           "HF":     HF_df,
                           "LF_HF":  LF_HF_df,
                           "AC":     AC_df,
                           "DC":     DC_df,
                           "AC_DC":  AC_DC_df,
                           "DFA_a1": DFA_a1_df,
                           "BSI": BSI_df,
                           "TINN": TINN_df,
                           "HRVi": HRVi_df,                           
                           "duration": duration_df,
                           "num_beats": num_beats_df}

        self.info_frames = ["duration",
                            "num_beats"]

        self.current_patient = 0


    def add_row(self, patient_number):
        for key, frame in self.dataframes.items():
            row = pd.DataFrame([np.zeros(len(self.columns))], columns=self.columns)
            row.rename(index={0:patient_number}, inplace=True)
            self.dataframes[key] = pd.concat([frame, row], axis=0)
            self.current_patient = patient_number

    def add_measurement(self, measurement, metric_type, timestamp, row_index = -1):
        """Modify entry in dataframe, defaults to most recent row but can
        specify a patient number using row_index. Awkward .loc.index repeated
        due to being burnt by creating copies of dataframes instead of references,
        so now I am scared."""
        metric_type = metric_type.replace("/","_")
        #TODO: find replacement strategy for if row_index checks - pick between integer or label indexing
        
        if row_index == -1:
            current_measurement = self.dataframes[metric_type].loc[self.dataframes[metric_type].index[row_index], timestamp]
        else:
            current_measurement = self.dataframes[metric_type].loc[row_index, timestamp]
            
        counter = 1

        #Check for existing value, if it exists add a new column, incrementing label with a number.
        while(current_measurement and not np.isnan(current_measurement)):
            insert_index = self.dataframes[metric_type].columns.get_loc(timestamp) + 1
            timestamp = timestamp.rstrip(" 1234567890") + str(counter)
            counter += 1

            if timestamp not in self.dataframes[metric_type]:
                self.dataframes[metric_type].insert(loc=insert_index,column=timestamp,value=0)

            if row_index == -1:
                current_measurement = self.dataframes[metric_type].loc[self.dataframes[metric_type].index[row_index], timestamp]
            else:
                current_measurement = self.dataframes[metric_type].loc[row_index, timestamp]

        if row_index == -1:
            self.dataframes[metric_type].loc[self.dataframes[metric_type].index[row_index], timestamp] = measurement
        else:
            self.dataframes[metric_type].loc[row_index, timestamp] = measurement

    def store_timestamp_results(self, results_dict, timestamp, patient_number):

        for result in results_dict.items():
            label = result[0]
            measurement = result[1]
            self.add_measurement(measurement, label, timestamp, row_index=patient_number)

    def carraige_return(self, row_index = -1):
        for key, frame in self.dataframes.items():
            if row_index == -1:
                self.dataframes[key].loc[self.dataframes[key].index[row_index], 'Abnormal Procedure End'] = 1
            else:
                current_measurement = self.dataframes[key].loc[row_index, 'Abnormal Procedure End'] = 1

        self.add_row(str(self.current_patient) + "_")

    def normalise_row(self, x, columns=[], mode="minmax", tag=None):
        if mode == "minmax":
            try:
                x = pd.to_numeric(x - np.nanmin(x[columns].values))
            except AttributeError:
                return x
        if np.nanmax(abs(x[columns].values)) == 0:
            pass

        elif mode == "by_tag":
            x = pd.to_numeric(x / x[tag])

        else:
            x = pd.to_numeric(x / np.nanmax(abs(x[columns].values)))
        return x

    def normalise_rows(self, columns=[], mode="minmax", stitched=False, tag=None):
        """Normalise all rows of frame from min=0 to max=1 ("minmax") or as a
        proportion of max ("max").

        Columns is a list of columns to take the min/max from, but the whole row
        will be normalised to these values. This means that a vasovagal event,
        for example, could have a negative or >1 value. """
        if mode == 'by_tag':
            if tag == None:
                print("Row normalised by tag, but no tag specified, defaulting to Consult Room")
                tag = "Consult Room"
        if stitched:
            for key, frame in self.stitched_frames.items():
                frame = frame.apply(self.normalise_row, axis=1, args=(columns, mode, tag))
                self.stitched_frames[key] = frame
        else:
            for key, frame in self.dataframes.items():
                frame = frame.apply(self.normalise_row, axis=1, args=(columns, mode, tag))
                self.dataframes[key] = frame

    def stitch_broken_procedures(self):
        """Join procedures split by an abnormal procedure end.

        Procedure start has an index NN, whereas procedure continuation has index NN_.
        This function finds all indexes containing an _, and creates two copies
        of the dataframe, one with the NN_ tags deleted and one the NN tags.
        The two dataframes are merged, filling NAN values in the continued set
        with values from the initial set. This imports the consult room reading into
        the continued function.

        Seems hacky.
        """
        #TODO: Separate and check trnd across these procedures in case of whack
        # consult room readings due to machine reconfigure.
        self.stitched_frames = {}
        for key, frame in self.dataframes.items():

            #Get indices of broken procedures
            continuations_mask = ["_" in index for index in self.dataframes[key].index]
            continuations_mask.append(False)

            # Create a frame of starts and finishes
            starts_removed = frame.drop(frame.index[continuations_mask[1:]], axis=0).replace({0:None})
            conts_removed = frame.drop(frame.index[continuations_mask[:-1]], axis=0)

            #Remove underscores from continuation indices so they can find their home
            starts_removed.index = starts_removed.index.map(lambda x: str(x).strip("_"))

            #backfill nans in starts_removed with conts_removed values
            self.stitched_frames[key] = starts_removed.combine_first(conts_removed)


    def finish(self):
        self.stitch_broken_procedures()

        for key, frame in self.stitched_frames.items():
            self.stitched_frames[key] = frame.replace({0: None})

        with pd.ExcelWriter(self.savepath) as writer:
            for key, frame in self.stitched_frames.items():
                frame.to_excel(writer, sheet_name=key.replace("/","_"))
