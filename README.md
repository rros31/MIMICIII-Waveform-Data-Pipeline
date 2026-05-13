# MIMIC-III Waveform Data Pipeline

A Python pipeline for extracting a cohort of mechanically-ventilated, propofol-sedated ICU patients from the MIMIC-III clinical database, downloading their matched waveform recordings, and computing Heart Rate Variability (HRV) metrics over the course of each stay.

> **Note:** This code is not actively maintained and is shared for reference. It is largely documented and functional.  
> Migrated from private repo: 14/05/2026.

---

## What it does

The pipeline has three broad stages:

### 1. Cohort Selection (`src/queries.py`, `src/exclusions.py`)
- Loads MIMIC-III CSVs (`ICUSTAYS`, `PATIENTS`, `CPTEVENTS`, `INPUTEVENTS_MV/CV`, `CHARTEVENTS`).
- Filters stays by length-of-stay (default 5–14 days).
- Keeps only patients who had **invasive mechanical ventilation** and received **propofol**.
- Optionally restricts to MICU patients.
- Matches each stay to its corresponding waveform recording by aligning admission timestamps (±14 days).
- Produces a dict of `Record` objects (`src/record.py`) keyed by hospital admission ID, saved as a pickle (`sedated_subset.pkl`).

### 2. Data Acquisition (`Examples/getEligiblePatients.py`)
- Downloads raw waveform files from PhysioNet (`mimic3wdb-matched`) for the selected patient IDs using `wget` and `BeautifulSoup`.
- Files land in `waveforms/<subject_id>/`.

### 3. HRV Analysis (`src/WaveformTools.py`, `src/HRV.py`)
- Reads waveform segments using `wfdb`, extracts the **ECG Lead II** or **PPG (PLETH)** channel.
- Detects R-peaks / PPG peaks via `wfdb.processing.XQRS` or `neurokit2`.
- Splits each recording into sliding windows (default 5 min) and computes a full HRV feature set per window:

| Domain | Metrics |
|--------|---------|
| Time | RMSSD, SDNN, pNN50 |
| Frequency (Welch) | VLF, LF, HF power, LF/HF ratio |
| Non-linear | DFA α1, AC/DC (PRSA), ANI |

- Results are collected into a `results_df` and exported to CSV.

---

## Repository layout

```
src/
  queries.py          - MIMICQuery class: loads CSVs, SQL filtering, drug/vent lookups
  record.py           - Record class: per-patient stay object
  exclusions.py       - Exclusions class: cohort filtering + waveform matching
  WaveformTools.py    - Waveform loading, R-peak detection, epoch splitting
  HRV.py              - Orchestrates all HRV metrics across epochs
  freq.py             - Frequency-domain HRV (Welch / Lomb-Scargle)
  time_metrics.py     - Time-domain HRV
  dfa.py              - Detrended Fluctuation Analysis
  PRSA.py             - Phase-Rectified Signal Averaging (AC/DC)
  ANI.py              - Analgesia Nociception Index
  geom.py             - Geometric HRV metrics (BSI, TINN, HRVi)
  drugProcess.py      - Drug chart extraction and rate timeseries (propofol/fentanyl)
  preprocess_chart_events.py - Chunked extraction of CHARTEVENTS for cohort
  results_df.py       - Results accumulator → CSV
  data_cleaning.py    - Signal cleaning utilities
  HR_filt.py          - HR filtering helpers
  epochs.py / patients.py - Thin list subclasses for type clarity
  loadingBar.py       - CLI progress bar
  patient_review_gui.py - Manual patient review GUI

Examples/
  getEligiblePatients.py  - End-to-end cohort selection + optional download
  processRassData.py      - RASS sedation score processing
  RassScoreswInfusion.py  - RASS scores aligned with drug infusion timelines
  Sedscoretest.py         - Sedation score exploration
  profileview.py          - Patient profile visualisation
  fun.py / play.py        - Ad-hoc exploration scripts
```

---

## Typical workflow

```python
# 1. Select cohort and save pickle
# run Examples/getEligiblePatients.py  (set downloadFiles=True to also fetch waveforms)

# 2. Pre-filter CHARTEVENTS (large file — run once)
from preprocess_chart_events import extract_patient_charts
extract_patient_charts('sedated_subset.pkl', 'FILT_CHART_EVENTS.csv')

# 3. Run HRV analysis on a patient
import pickle
from WaveformTools import WaveformTools

with open('sedated_subset.pkl', 'rb') as f:
    records = pickle.load(f)

stay_id = list(records.keys())[0]
wt = WaveformTools(records[stay_id])
hrv_results = wt.process_HRV_all_epochs(signal='ppg')  # or 'ecg'
```

---

## Data requirements

The pipeline expects MIMIC-III clinical CSVs in a `M3_Clincial/` directory:

- `PATIENTS.csv`
- `ICUSTAYS.csv`
- `CPTEVENTS.csv`
- `INPUTEVENTS_MV.csv` / `INPUTEVENTS_CV.csv`
- `CHARTEVENTS.csv` (large; pre-filtered via `preprocess_chart_events.py`)

Waveform data is downloaded from PhysioNet (`mimic3wdb-matched`) into `waveforms/`.

Access to MIMIC-III requires credentialed PhysioNet account and completion of the required training course.

---

## Dependencies

`wfdb`, `neurokit2`, `pandas`, `pandasql`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `requests`, `beautifulsoup4`, `wget`, `dask`
