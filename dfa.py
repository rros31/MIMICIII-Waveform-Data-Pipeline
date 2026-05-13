# -*- coding: utf-8 -*-
"""
Created on Tue May 10 08:48:33 2022

@author: cca78
"""
import numpy as np
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt

def fit_trend(data, indices, porder = 1):

    coeffs = poly.polyfit(indices, data, deg=porder)
    return coeffs

def window_reshape(data, n):

    n = int(n)
    datalen = len(data)
    chunks = data[:datalen - datalen % n]
    chunks = chunks.reshape(len(chunks) // n, n)

    return chunks

def detrend_chunks(chunks, porder=1):
    n=chunks.shape[1]
    x = np.arange(n)
    #TODO: Remove rcond when pandas updates it's cython version

    coeffs = poly.polyfit(x, chunks.T, porder, rcond = n * 2e-16)

    trends = np.zeros(chunks.shape)

    for j in range(chunks.shape[0]):
        for i in range(porder + 1):
            trends[j,:] += coeffs[i,j] * (x ** i)

    return chunks - trends

def get_rms(detrended_chunks, methods = {"perchunk": "meansquare",
                                         "perset": "rootmean"} ):
    if methods["perchunk"] == "mean":
        halfsum = np.mean(detrended_chunks, axis = 1)
    elif methods["perchunk"] == "meansquare":
        halfsum = np.mean(detrended_chunks ** 2, axis=1)
    elif methods["perchunk"] == "rootmean":
        halfsum = np.sqrt(np.mean(detrended_chunks, axis=1))
    elif methods["perchunk"] == "rootmeansquare":
        halfsum = np.sqrt(np.mean(detrended_chunks**2, axis=1))

    if methods["perset"] == "mean":
        rms = np.mean(halfsum)
    elif methods["perset"] == "meansquare":
        rms = np.mean(halfsum ** 2)
    elif methods["perset"] == "rootmean":
        rms = np.sqrt(np.mean(halfsum))
    elif methods["perset"] == "rootmeansquare":
        rms = np.sqrt(np.mean(halfsum ** 2))
    return rms


def pre_integrate(data):
    mean = np.mean(data)
    integral = np.cumsum(data - mean)
    return integral

def plot_dfa(f_n,
             n_vec,
             coeffs,
             vectors,
             ax = None):

    if not ax:
        fig, ax = plt.subplots(1,1)

    ax.plot(np.log10(n_vec), np.log10(f_n), 'x')
    ax.plot(np.log10(vectors["short_n"]),vectors["short_vec"], label = "alpha_1 = {}".format(coeffs["alpha_1"][1]))
    ax.plot(np.log10(vectors["long_n"]),vectors["long_vec"], label = "alpha_2 = {}".format(coeffs["alpha_2"][1]))
    ax.set_xlabel("log10 beats")
    ax.set_ylabel("log10 fluctuations")
    ax.set_title("Detrended Fluctuation Analysis Results")
    plt.grid(which="both")
    plt.legend()

def dfa(data,
        indices,
        porder=1,
        n_vec = np.zeros(0),
        short_range=[4,12],
        long_range = [13,64],
        both_directions=True,
        rms_methods = {"perchunk": "meansquare",
                       "perset": "rootmean"},
        plot=True,
        ax=None):

    if not n_vec.any():
        n_vec = np.arange(porder + 3, len(data) / 3)

    # Convert to ms if reqd
    if data[1] > 2:
        data = data / 1000

    integrated = pre_integrate(data)

    f_n = np.zeros(len(n_vec))

    for i, n in enumerate(n_vec):
        reshaped = window_reshape(integrated, n)

        if both_directions:
            reshaped = np.concatenate((reshaped, window_reshape(integrated[::-1], n)))

        detrended = detrend_chunks(reshaped)

        f_n[i] = get_rms(detrended, methods=rms_methods)

    try:
        coeffs = fit_params(f_n, n_vec)
    except:
        print("You've tried to root a negative value in the rms function, so the polynomial fitter is freaking out")
        coeffs={"alpha_1":[0,0],
                "alpha_2":[0,0]}

    vectors = get_slope_vecs(coeffs,
                             n_vec,
                             short_range,
                             long_range)
    if plot:
        plot_dfa(f_n,
                 n_vec,
                 coeffs,
                 vectors,
                 ax)


    return {"f_n": f_n,
            "n_vec": n_vec,
            "coeffs": coeffs,
            "vectors":vectors
            }

def fit_params(f_n, n_vec, short_range = [4, 12], long_range = [13,64]):
    short_indices = [np.argwhere(n_vec > short_range[0])[0][0],
                     np.argwhere(n_vec > short_range[1])[0][0]]
    long_indices = [np.argwhere(n_vec > long_range[0])[0][0],
                    np.argwhere(n_vec >= long_range[1])[0][0]]

    #TODO: Remove rcond when pandas updates it's cython version
    coeffs_short = poly.polyfit(np.log10(n_vec[short_indices[0]:short_indices[1]]),
                                np.log10(f_n[short_indices[0]:short_indices[1]]), deg=1, rcond= len(n_vec[short_indices[0]:short_indices[1]]) * 2e-16)
    coeffs_long = poly.polyfit(np.log10(n_vec[long_indices[0]:long_indices[1]]),
                                np.log10(f_n[long_indices[0]:long_indices[1]]), deg=1, rcond= len(n_vec[long_indices[0]:long_indices[1]]) * 2e-16)

    return {"alpha_1": coeffs_short,
            "alpha_2": coeffs_long}

def get_slope_vecs(coeffs,
                   n_vec,
                   short_range=[4,12],
                   long_range=[13,64]):

    short_n = np.linspace(*short_range, num=np.diff(short_range)[0] + 1)
    long_n = np.linspace(*long_range, num=np.diff(long_range)[0] + 1)

    short_vec = coeffs["alpha_1"][0] + coeffs["alpha_1"][1] * np.log10(short_n)
    long_vec = coeffs["alpha_2"][0] + coeffs["alpha_2"][1] * np.log10(long_n)

    return {"short_n": short_n,
            "long_n": long_n,
            "short_vec": short_vec,
            "long_vec": long_vec}

# Test Code

# plt.close('all')

# datalen = 100000
# data = np.random.randn(datalen)
# porder = 1
# indices = np.arange(datalen)
# n_vec = np.arange(4, 65)
# short_range = [4, 12]
# long_range = [13, 63]


# dfa_results = dfa(data, indices, n_vec = np.arange(4,65))

# short_n = dfa_results["vectors"]["short_n"]
# long_n = dfa_results["vectors"]["long_n"]
# short_vec = dfa_results["vectors"]["short_vec"]
# long_vec = dfa_results["vectors"]["long_vec"]

# plt.figure()
# plt.plot(np.log10(dfa_results["n_vec"]), np.log10(dfa_results["f_n"]), 'x')
# plt.plot(np.log10(short_n), short_vec)
# plt.plot(np.log10(long_n), long_vec)
# print("Alpha1 = {}".format(dfa_results["coeffs"]["alpha_1"][1]))
# print("Alpha2 = {}".format(dfa_results["coeffs"]["alpha_2"][1]))
