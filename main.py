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

import os
import argparse
import json
import datetime
from rtlsdr import RtlSdr
from pylab import *
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants

from pssdrift import *
import soapy_log_handle

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


 # Load Zadoof sequencies
def get_zadoof_seqs (filename):
    f = open(filename,'rb');
    bdata = np.fromfile(f, '<f4')
    cdata = np.vectorize(complex)(bdata[range(0,len(bdata),2)] , bdata[range(1,len(bdata),2)])
    return cdata


# Constants
VERSION="0.1-rc1"
RESAMPLE_FACTOR = 20
PSS_STEP = 9600
SEARCH_WINDOW = 150
PREAMBLE=20

# variables
fs=1.92e6
fc=806e6
chan=0
gain=30

AUX_BUFFER_SIZE = 20*1024


if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-f", '--frequency', type=int, dest='frequency',  help="Set LTE center frequency of the channel (Hz)", default=fc)
    parser.add_argument("-g", '--gain', type=int, dest='gain',  help="Gain", default=gain)
    parser.add_argument("-t", "--time", type=int, dest='time', help="Seconds collecting data on LTE frequency", default=1)
    parser.add_argument("-j", '--json-file', dest='json', type=str,  help="Set the json file where results will be written", default=None)
    parser.add_argument("-d", '--debug', dest='debug',  help="enable debug mode with plots", action='store_true', default=False)
    args = parser.parse_args()

    print("#########################################")
    print("#      = pyLTESS-Track v" + VERSION + " =       #")
    print("#                                       #")
    print("# A precise and fast frequency offset   #")
    print("# estimation for low-cost SDR platforms #")
    print("# -- The Electrosense Team              #")
    print("########################################")

    fc = args.frequency
    gain = args.gain
    sampling_time = args.time

    # Look at for SDR devices
    sdr_list = SoapySDR.Device.enumerate()
    index=0
    sdr_devices = []
    print("")
    print("Available SDR devices: ")
    for sdr in sdr_list:
        if sdr["driver"]=="audio":
            pass
        else:
            print("   - [%d] %s (%s)" % (index, sdr["label"], sdr["driver"]) )
            sdr_devices.append(sdr)
            index=index+1

    try:
        print("")
        sdr_index=int(input('Choose SDR device [0-' + str(len(sdr_devices)-1) + ']: ' ))
    except ValueError:
        print("[Error] You must enter a number of the list")
        sys.exit(-1)

    args_sdr = sdr_devices[sdr_index]

    # Set SDR and read samples
    sdr = SoapySDR.Device(args_sdr)
    sdr.setSampleRate(SOAPY_SDR_RX, chan, int(fs))
    sdr.setBandwidth(SOAPY_SDR_RX, chan, int(fs))
    sdr.setFrequency(SOAPY_SDR_RX, chan, int(fc))
    sdr.setGain(SOAPY_SDR_RX,chan,gain)

    rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [chan])
    sdr.activateStream(rxStream)

    rxBuffs = np.array([], np.complex64)
    rxBuff = np.array([0]*AUX_BUFFER_SIZE, np.complex64)

    TOTAL_BUFFER_SIZE = int(fs*args.time) # 1 second of data

    iters = int(ceil(TOTAL_BUFFER_SIZE/AUX_BUFFER_SIZE))

    print("[LTESSTRACK] Reading for %d seconds at %d MHz with gain=%d ... " % (args.time, args.frequency, args.gain))
    acq_time = datetime.datetime.now()

    for i in range(0,iters):
        sr = sdr.readStream(rxStream, [rxBuff], len(rxBuff))

        if sr.ret > 0:
            rxBuffs = np.concatenate((rxBuffs, rxBuff[:sr.ret]))

    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)

    samples = rxBuffs

    if (args.debug):
        # use matplotlib to estimate and plot the PSD
        psd(samples, NFFT=1024, Fs=fs/1e6, Fc=fc/1e6)
        xlabel('Frequency (MHz)')
        ylabel('Relative power (dB)')
        show()

    print("[LTESSTRACK] Estimating local oscilator error .... ")
    # load zadoof sequences (in time)
    Z_sequences = np.array([get_zadoof_seqs("lte/25-Zadoff.bin"),get_zadoof_seqs("lte/29-Zadoff.bin"),get_zadoof_seqs("lte/34-Zadoff.bin")])

    # Get drift by analyzing the PSS time of arrival
    [PPM, delta_f] = get_drift(samples, Z_sequences, PREAMBLE, PSS_STEP, SEARCH_WINDOW, RESAMPLE_FACTOR, fs, debug_plot=args.debug)

    print("[LTESSTRACK] Local oscilator error: %.8f PPM - [%.2f Hz]" % (PPM,delta_f))

    if (args.json):
        data={}
        data['datetime']=str(acq_time)
        data['type']=args_sdr["label"] + " "  +args_sdr["driver"]
        data['fc']=args.frequency
        data['gain']=args.gain
        data['fs']=fs
        data['sampling_time']=args.time
        data['ppm']=PPM
        data['confidence']=0

        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print("[LTESSTRACK] Results saved in " + args.json)
