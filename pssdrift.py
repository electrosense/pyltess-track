#!/usr/bin/python
#
#   Copyright (C) Electrosense 2019
#   This program is free software: you can redistribute it and/or modify
#
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see http://www.gnu.org/licenses/.
#
#   Authors: Roberto Calvo-Palomino <roberto.calvo [at] imdea [dot] org>
#

from pylab import *
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

# get_peaks: get PSS peaks jumping from the last position known that was a valid peak
# Output:
#   - peaksV: vector with the correlation value of the peaks found
#   - peaksL: vector with the location value of the peaks found
#   -
def get_peaks (iq, pss_step, search_window, resample_factor, z_sequence, th_corr, debug_plot = False):

    SAFE_WINDOW = 60;

    index_done = 0

    start_i = index_done + pss_step - search_window
    end_i = index_done + pss_step + search_window + 1

    peak_list = [];

    while (end_i < len(iq)):

        slice = iq[start_i:end_i]

        scaler = MinMaxScaler(feature_range=(0, 1))

        # Correlation between template and slice signal
        res_corr = abs(signal.correlate(slice, z_sequence))
        # Normalization
        res_corr = np.reshape((res_corr), (-1, 1))
        res_corr = scaler.fit_transform(res_corr)
        # Trick to speed up the whole process.
        # Upsampling the correlaiton result (thanks Fabio!)
        res_corr_up = signal.resample(res_corr, len(res_corr)*resample_factor)

        # Find peaks in the correlation result
        x = np.resize(res_corr_up,len(res_corr_up),)
        peaks, _ = signal.find_peaks(x, distance=(len(slice)*resample_factor)-2, height=th_corr)


        if (len(peaks) == 0):
            print("[WARNING] No peak detected, corr_factor=%.2f\n" % th_corr);
            peak_list.append(None)
        else:
            p = start_i + (peaks[0])/resample_factor -1;
            peak_list.append(p)


        # No peak detected in this iteration -> No PSS detected
        # Move PSS_STEP forwards from start_i
        if (peak_list[-1] is None):
            start_i = start_i + pss_step;
            end_i = end_i + pss_step;
        else:
            # Peak was found -> Move PSS_STEP forwards from current peak
            index_done = int(round(peak_list[-1]))
            start_i = index_done + pss_step - search_window
            end_i = index_done + pss_step + search_window;


        if (debug_plot):
            xnew = np.linspace(0, len(res_corr), len(res_corr)*resample_factor, endpoint=False)
            plt.figure(figsize=(14,5))
            plt.plot(xnew, res_corr_up, '.-', label="upsampled")
            plt.plot(res_corr, 'ro-', label="original")


    return np.array(peak_list)

# Analyze the peaks of PSS to estimate and compute linear regression
# Inputs:
#    - peaks: vector of peaks position founded.
#    - pss_step: distance between PSS in I/Q samples
#    - degree: degree of the polinomial regresion.

def analyze_drift (peaks, pss_step, degree, debug_plot = False ):

    pss_detected = peaks - peaks[0]

    x = np.array(list(range(0,len(peaks))))

    cumm_drift = pss_detected - x*pss_step

    p = np.polyfit(x,cumm_drift,1)
    y = np.polyval(p,x)

    PPM= ((y[-1]-y[0])/((x[-1]-x[0])*pss_step))*1e6;


    if (debug_plot):
        t = pss_step / 1.92e6
        plt.figure(figsize=(14,5))
        plt.plot(x*t,cumm_drift, 'o', label='drift')
        plt.plot(x*t,y, '.-' ,label='slope')
        plt.xlabel('time (seconds)')
        plt.ylabel('cumm drift (IQ samples)')
        plt.legend(fontsize=15)
        plt.grid(True)


    return PPM



# Get proper Zadoof sequence
# Return:
#   - lpeaks:
#   - th_learned
#   - sequence_zadoof
def get_drift (iq, z_sequences, preamble, pss_step, search_window, resample_factor, fs, debug_plot=False):

    #training_samples = len(iq)
    training_samples = pss_step * preamble

    # Correlation with the zadoof templates over the training samples
    corr=np.array([signal.correlate(iq[:training_samples], (z_sequences[0]))])
    corr=np.append(corr, [np.array(signal.correlate(iq[:training_samples], (z_sequences[1])))],0)
    corr=np.append(corr, [np.array(signal.correlate(iq[:training_samples], (z_sequences[2])))],0)

    # Normalize correlation
    scaler = MinMaxScaler(feature_range=(0, 1))


    data = ([np.reshape(abs(corr[0]), (-1, 1))])
    data = np.append(data, [np.reshape(abs(corr[1]), (-1, 1))],0)
    data = np.append(data, [np.reshape(abs(corr[2]), (-1, 1))],0)

    scaler.fit_transform(np.concatenate( (data[0], data[1], data[2]), axis=0))

    for i in range(0,data.shape[0]):
        data[i] = scaler.transform(data[i])

    max_corr = 0.0
    seq = -1
    l_peaks = None
    th_win = None

    for i in range(0,data.shape[0]):
        # learn the threshold

        tmp_sorted = data[i][0:training_samples]
        tmp_sorted = np.resize(tmp_sorted,(len(tmp_sorted),))
        tmp_sorted=np.sort(tmp_sorted)[::-1]  # reverse order (descendent)


        th_learned=(tmp_sorted[preamble] + tmp_sorted[preamble*2+1])/2
        th_learned=th_learned*0.70
        print("th_learned[seq=%d]: %.2f" % (i,th_learned))
        x = np.resize(data[i],len(data[i]),)

        peaks, _ = signal.find_peaks(x[0:training_samples], distance=(pss_step-search_window), height=th_learned)
        p_value = max(x[peaks])
        if (p_value > max_corr):
            max_corr = p_value
            l_peaks = peaks;
            seq = i
            th_win = th_learned


    print("Winning sequence: " + str(seq))
    if ( len ( np.where (abs(diff(peaks)-pss_step) > 10 )[0]) > 0 ):
        print("[WARNING] Some PSS detected are further than %d +- 10 I/Q samples\n" % (pss_step))


    if (debug_plot):
        x = np.resize(data[seq],len(data[seq]),)
        plt.figure()
        plt.plot(x[0:training_samples])
        plt.plot(l_peaks, x[l_peaks], "x")
        #plt.xlim(0, 50000)
        plt.show()


    # We assume peaks are properly located if they are in a range of 10 samples from the expected position
    valid_peaks = np.where ((np.diff(l_peaks)-pss_step) < 10)
    if (len(valid_peaks)==0):
            print('[ERROR] No valid PSS at the begining, skipping file\n')
            sys.exit(-1)

    last_valid_peak = l_peaks[valid_peaks[0][-1]+1]

    pss_detected = get_peaks(iq[last_valid_peak:], pss_step, search_window, resample_factor, z_sequences[seq], th_win, False)

    PPM = analyze_drift(pss_detected, pss_step, 1, True)

    delta_f=(PPM*1e-6)*fs;

    return PPM, delta_f
