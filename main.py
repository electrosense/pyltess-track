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
TOTAL_BUFFER_SIZE = int(fs*1) # 1 second of data

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

args = sdr_devices[sdr_index]

# Set SDR and read samples
sdr = SoapySDR.Device(args)
sdr.setSampleRate(SOAPY_SDR_RX, chan, int(fs))
sdr.setBandwidth(SOAPY_SDR_RX, chan, int(fs))
sdr.setFrequency(SOAPY_SDR_RX, chan, int(fc))
sdr.setGain(SOAPY_SDR_RX,chan,gain)

rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [chan])
sdr.activateStream(rxStream)

rxBuffs = np.array([], np.complex64)
rxBuff = np.array([0]*AUX_BUFFER_SIZE, np.complex64)

iters = int(ceil(TOTAL_BUFFER_SIZE/AUX_BUFFER_SIZE))

for i in range(0,iters):
    sr = sdr.readStream(rxStream, [rxBuff], len(rxBuff))

    if sr.ret > 0:
        rxBuffs = np.concatenate((rxBuffs, rxBuff[:sr.ret]))

sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)

samples = rxBuffs

# use matplotlib to estimate and plot the PSD
psd(samples, NFFT=1024, Fs=fs/1e6, Fc=fc/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')
show()

# load zadoof sequences (in time)
Z_sequences = np.array([get_zadoof_seqs("lte/25-Zadoff.bin"),get_zadoof_seqs("lte/29-Zadoff.bin"),get_zadoof_seqs("lte/34-Zadoff.bin")])

# Get drift by analyzing the PSS time of arrival
[PPM, delta_f] = get_drift(samples, Z_sequences, PREAMBLE, PSS_STEP, SEARCH_WINDOW, RESAMPLE_FACTOR, fs, debug_plot=True)

print("Local Oscilator error: %.8f PPM - %.2f Hz\n" % (PPM,delta_f))
