import numpy as np
import pywt
from scipy.interpolate import interp1d
import scipy.signal as signal
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
def rr_interval_filter(rr_intervals, window_size=20, threshold_factor=2):
    """
    Filters out artifacts from the R-R interval series using the method described by Logier et al.
    
    Parameters:
        rr_intervals (list or np.array): The input series of R-R intervals in milliseconds.
        window_size (int): Size of the moving window to calculate mean and standard deviation.
        threshold_factor (float): Factor to define the thresholds as mean ± threshold_factor * std.
    
    Returns:
        np.array: The filtered R-R intervals.
    """
    
    # Initialize variables
    rr_intervals = np.array(rr_intervals)
    filtered_rr = rr_intervals.copy()
    n = len(rr_intervals)
   
    # Process each sample
    for i in range(window_size, n-1):
        # Compute mean and std for the previous window
        window = rr_intervals[i-window_size:i]
        m20 = np.mean(window)
        sigma20 = np.std(window)
        
        # Set the thresholds
        lower_threshold = m20 - threshold_factor * sigma20
        upper_threshold = m20 + threshold_factor * sigma20
        
        # Check if the current sample is within the thresholds
        if not (lower_threshold <= rr_intervals[i] <= upper_threshold):
            # Apply the artifact conditions C1, C2, and C3
            if (
                (i < n-1 and rr_intervals[i] < lower_threshold and rr_intervals[i+1] > upper_threshold) or  # C1
                (rr_intervals[i] < 0.75 * rr_intervals[i-1] or rr_intervals[i+1] < 0.75 * rr_intervals[i-1]) or  # C2
                (rr_intervals[i] > 1.75 * rr_intervals[i-1])  # C3
            ):
                # Artifact detected, apply linear interpolation
                # Find the next valid sample
                for j in range(i+1, n):
                    if lower_threshold <= rr_intervals[j] <= upper_threshold:
                        break
                else:
                    j = n  # If no valid sample found
                
                # Linear interpolation between valid samples
                rr0 = rr_intervals[i-1]
                rrm = rr_intervals[j]
                time_interval = j - (i - 1)
                
                for k in range(i, j):
                    filtered_rr[k] = rr0 + (rrm - rr0) * (k - i + 1) / time_interval
    
    return filtered_rr


def normalize_rr_intervals(rr_intervals, fs=125, resample_fs=8, window_size=64):
    """
    Processes and normalizes R-R intervals as described in the method.

    Parameters:
        rr_intervals (list or np.array): The R-R intervals in milliseconds.
        fs (int): Original sampling frequency of the ECG signal (default is 250 Hz).
        resample_fs (int): Frequency to resample the R-R intervals (default is 8 Hz).
        window_size (int): Size of the moving window for normalization in seconds (default is 64 seconds).

    Returns:
        np.array: The normalized R-R intervals.
    """
    
    # # 1. Resample the R-R interval series to 8 Hz using linear interpolation
    # time_original = np.cumsum(rr_intervals)   # Convert R-R intervals to cumulative time in seconds
    # time_resampled = np.arange(0, time_original[-1], 1 / resample_fs)  # New time points for 8 Hz
    
    # # Perform linear interpolation
    # interpolator = interp1d(time_original, rr_intervals, kind='linear', fill_value='extrapolate')
    
    
    
    
 
        
        # Step 1: Compute the mean (M) and subtract from each value
    M = np.mean(rr_intervals)
    rr_prime = rr_intervals - M
        
     # Step 2: Compute the norm (S) and divide each value by S
    S = np.sqrt(np.sum(rr_prime ** 2))
    rr_double_prime = rr_prime / S if S != 0 else rr_prime
        
    # Store the normalized values in the output array
    # rr_normalized[i:i + samples_per_window] = rr_double_prime
    
    return rr_double_prime


def wavelet_high_pass_filter(rr_intervals, wavelet='db4', low_freq=0.15, high_freq=0.5, resample_fs=8):
    """
    Apply a high-pass filter between 0.15 and 0.5 Hz using Daubechies wavelet transform.
    
    Parameters:
        rr_intervals (np.array): The normalized R-R interval series.
        wavelet (str): The wavelet to use (default is 'db4').
        low_freq (float): The lower bound of the high-pass filter in Hz (default 0.15 Hz).
        high_freq (float): The upper bound of the high-pass filter in Hz (default 0.5 Hz).
        resample_fs (int): The sampling frequency of the R-R intervals (default 8 Hz).
        
    Returns:
        np.array: The high-pass filtered R-R intervals.
    """
    
    # Perform discrete wavelet transform (DWT) on the R-R intervals using Daubechies wavelet
    coeffs = pywt.wavedec(rr_intervals, wavelet)
    
    # Calculate the scale corresponding to the target frequencies
    # Frequency at level 'i' = resample_fs / (2^(i + 1)) for a dyadic wavelet decomposition
    # For Daubechies wavelets, this approximation helps identify the scales
    freqs = [resample_fs / (2 ** (i + 1)) for i in range(len(coeffs) - 1)]
    
    # Determine which coefficients to keep based on frequency range (0.15–0.5 Hz)
    filtered_coeffs = []
    
    for i, c in enumerate(coeffs):
        # Skip the approximation coefficients (i = 0)
        if i == 0:
            filtered_coeffs.append(np.zeros_like(c))  # Zero out approximation (low frequencies)
        else:
            # Keep detail coefficients corresponding to desired frequency range
            if low_freq <= freqs[i - 1] <= high_freq:
                filtered_coeffs.append(c)  # Keep this level
            else:
                filtered_coeffs.append(np.zeros_like(c))  # Zero out other levels
    
    # Reconstruct the signal using the inverse wavelet transform
    rr_filtered = pywt.waverec(filtered_coeffs, wavelet)
    
    # Truncate or pad the result to the original length
    rr_filtered = rr_filtered[:len(rr_intervals)]
    
    return rr_filtered

# Design a Butterworth band-pass filter
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyquist = 0.5 * fs  # Nyquist frequency
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut=0.15, highcut=0.5, fs=8, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y



def find_envelopes(rr_filtered, sampling_freq):
    """
    Find local maxima and minima to compute upper and lower envelopes.
    
    Parameters:
        rr_filtered (np.array): The filtered R-R intervals signal.
        sampling_freq (float): Sampling frequency of the signal (default is 8 Hz).
        
    Returns:
        tuple: Upper envelope, lower envelope, time vector.
    """
    # Time vector
    time = np.arange(len(rr_filtered)) / sampling_freq

    # Find local maxima and minima
    peaks_max, _ = signal.find_peaks(rr_filtered)
    peaks_min, _ = signal.find_peaks(-rr_filtered)

    # Interpolate to create upper and lower envelopes
    upper_envelope = np.interp(time, time[peaks_max], rr_filtered[peaks_max])
    lower_envelope = np.interp(time, time[peaks_min], rr_filtered[peaks_min])

    return upper_envelope, lower_envelope, time,peaks_min,peaks_max

def compute_auc(rr_filtered, sampling_freq=8, window_size_sec=16):
    """
    Compute areas under the curve (AUC) between envelopes in 16-second sub-windows.
    
    Parameters:
        rr_filtered (np.array): The filtered R-R intervals signal.
        sampling_freq (float): Sampling frequency of the signal.
        window_size_sec (int): Size of each sub-window in seconds (default 16 seconds).
        
    Returns:
        float: AUCmin, the minimum of the areas between envelopes.
    """
    # Find envelopes
    upper_envelope, lower_envelope, time,peaks_min,peaks_max = find_envelopes(rr_filtered, sampling_freq)
    
    # Sub-window size in samples
    window_size = int(window_size_sec * sampling_freq)
    
    # Initialize an array to store the AUCs
    aucs = []
    # print(f"L:{len(rr_filtered)}")
    # Loop through the 16-second windows and compute the AUC between envelopes
    for i in range(0, len(rr_filtered), window_size):
        # print(i)
        upper_window = upper_envelope[i:i+window_size]
        lower_window = lower_envelope[i:i+window_size]
        time_window = time[i:i+window_size]
        # plt.figure()
        # plt.plot(time_window,rr_filtered[i:i+window_size])
        # plt.plot(time_window,upper_window,'o')
        # plt.plot(time_window,lower_window,'o')
        # plt.plot(peaks_min,rr_filtered[peaks_min],'o')
        # plt.plot(peaks_max,rr_filtered[peaks_max],'o')
        # Compute AUC between the upper and lower envelopes using trapezoidal rule
        auc_upper = np.trapz(upper_window, time_window)
        auc_lower = np.trapz(lower_window, time_window)
        
        # Area between envelopes (AUC)
        auc = auc_upper - auc_lower
        aucs.append(auc)
    
    # Find the minimum AUC
    aucs[aucs==0]= 100000 #Attempt to
    auc_min = min(aucs)
    
    if auc_min == 100000:
        auc_min =0
    return auc_min, aucs

def ani_analyis(intervals,samplingfreq=125,resample_fs=8):

     # 1. Resample the R-R interval series to 8 Hz using linear interpolation
    time_original = np.cumsum(intervals)   # Convert R-R intervals to cumulative time in seconds
    time_resampled = np.arange(0, time_original[-1], 1 / resample_fs)  # New time points for 8 Hz
    
    # Perform linear interpolation
    interpolator = interp1d(time_original, intervals, kind='linear', fill_value='extrapolate')
    intervals = interpolator(time_resampled)
    # print(len(intervals))
    window_size=(64*8)
    anis=[]
    for i in range(0,len(intervals)-window_size,window_size):
        # print(i)
        RRFilt = intervals[i:i+window_size] #rr_interval_filter(intervals[i:i+window_size])
        RRNORMALISE = normalize_rr_intervals(RRFilt)

        # print(len(RRNORMALISE)
        RR_HF = bandpass_filter(RRNORMALISE)
        
        Auc_min, auc = compute_auc(RR_HF)
        anis.append(100*(5.1*Auc_min+1.2)/12.8)

    return np.mean(anis)