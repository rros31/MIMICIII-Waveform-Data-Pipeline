import numpy as np
from scipy.signal import butter, filtfilt, lfilter
from scipy.interpolate import interp1d
def resample_rr_intervals(RR_intervals, resample_interval=0.1):
    """
    Resamples RR intervals to a regular time grid using linear interpolation.
    
    Parameters:
    RR_intervals (numpy array): The RR intervals in milliseconds.
    resample_interval (int, optional): The interval (in seconds) at which to resample the RR intervals. Default is 1 second.
    
    Returns:
    numpy array: The resampled RR intervals at the new time points.
    numpy array: The new time points corresponding to the resampled RR intervals.
    """
    # Calculate original timestamps (cumulative sum of RR intervals)
    original_time = np.cumsum(RR_intervals)  # Convert to seconds
    
    # Define the new time points for resampling (e.g., every 1 second)
    new_time = np.arange(0, original_time[-1], resample_interval)
    
    # Interpolate RR intervals to the new time points
    interpolator = interp1d(original_time, RR_intervals, kind='linear', fill_value="extrapolate")
    RR_resampled = interpolator(new_time)
    
    return RR_resampled, new_time


def highpass_HR(RR_ints,
        cutoff_frequency_l= 0.00001,
        cutoff_frequency_h=0.1,
        average_HR = 100):
    
    RR_inter, RR_time = resample_rr_intervals(RR_ints) 
    HR =60/RR_inter
    sampling_rate = 10
    # Create a Butterworth high-pass filter
    b, a = butter(N=2, Wn=[cutoff_frequency_l,cutoff_frequency_h], btype='bandpass', fs=sampling_rate)
    
    # Apply the high-pass filter to the HR data
    # heart_rate_filtered = filtfilt(b, a, HR_filt )
    return  lfilter(b, a, HR-average_HR )
