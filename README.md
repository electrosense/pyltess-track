# pyltess-track

A precise and fast frequency offset estimation for low-cost SDR platforms implemented in python. This impementation can work efficently in embedded systems such as Raspberry Pi, estimating the frequency offset of the internal oscillator in less than 2 seconds.


**pyltess-track** is the open source implementation part of the paper named **LTESS-track: A Precise and Fast Frequency Offset Estimation for low-cost SDR Platforms** published in *ACM Workshop on Wireless Network Testbeds, Experimental evaluation & CHaracterization (ACM WiNTECH 2017), 16-20 October 2017, Snowbird, Utah, USA* by Roberto Calvo-Palomino, Fabio Ricciato, Domenico Giustiniano and Vincent Lenders ([PDF](http://eprints.networks.imdea.org/id/document/4484))

There is a MATLAB version of pyltess-track available [here](https://github.com/electrosense/LTESS-track)

## License

```
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.
```

## Usage

```
$ pyltess-track.py --help
usage: pyltess-track.py [-h] [-s SOURCE] [-f FREQUENCY] [-g GAIN] [-t TIME]
                        [-j JSON] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Set default SDR source device to use (default: -1)
  -f FREQUENCY, --frequency FREQUENCY
                        Set LTE center frequency of the channel (Hz) (default:
                        806000000.0)
  -g GAIN, --gain GAIN  Gain (default: 30)
  -t TIME, --time TIME  Seconds collecting data on LTE frequency (default: 1)
  -j JSON, --json-file JSON
                        Set the json file where results will be written
                        (default: None)
  -d, --debug           enable debug mode with plots (default: False)
```

## Running

**pyltess-track** makes use of the PSS (Primary Synchronization Signal) of LTE to estimate the FOC. Make sure that you tune properly to the center frequency of LTE signal. Tipically following frequencies will work: 796 MHz, 806 MHz and 816 MHz.

```
$ pyltess-track.py

#########################################
#      = pyLTESS-Track v1.0-rc1 =       #
#                                       #
# A precise and fast frequency offset   #
# estimation for low-cost SDR platforms #
#                                       #
# -- The Electrosense Team              #
#########################################
Detached kernel driver
Found Rafael Micro R820T tuner
Reattached kernel driver

Available SDR devices:
   - [0] Generic RTL2832U OEM :: 00000001 (rtlsdr)

Choose SDR device [0-0]: 0

[LTESSTRACK] SDR device selected: rtlsdr - Generic RTL2832U OEM :: 00000001
Detached kernel driver
Found Rafael Micro R820T tuner
[R82XX] PLL not locked!
[INFO] Using format CF32.
[LTESSTRACK] Reading for 1 seconds at 806000000 MHz with gain=30 ...
[LTESSTRACK] Estimating local oscilator error ....
[LTESSTRACK] Warning: Some PSS detected are further than 9600 +- 10 I/Q samples
[LTESSTRACK] Local oscilator error: -0.40376887 PPM - [-0.78 Hz], confidence=0.800
Reattached kernel driver
```

## Examples

* Set frequency and sampling time of 3 seconds
```
$ pyltess-track.py -s 0 -f 806000000 -t 3
```

* Set frequency and sampling time of 3 seconds
```
$ pyltess-track.py -s 0 -f 806000000 -t 3
```

* Export results to JSON filename
```
$ pyltess-track.py -s 0 -f 806000000 -t 2 -j ./foc-sdr.json
```

* JSON output
```json
{
    "datetime": "2019-12-23 11:48:28.381867",
    "type": "Generic RTL2832U OEM :: 00000001 rtlsdr",
    "fc": 806000000,
    "fs": 1920000,
    "gain": 30,
    "sampling_time": 2,
    "ppm": -0.4945936421151772,
    "confidence": 0.9973045822102425
}
```

## Deploy

* Create debian package
```
$ python3 setup.py --command-packages=stdeb.command bdist_deb
```
