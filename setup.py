#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
from setuptools import setup, find_packages


setup(name='pyltess-track',
      version='1.0-rc1',
      description='Fast Frequency Offset Estimation for SDR devices',
      author='Roberto Calvo-Palomino',
      author_email='roberto.calvo@imdea.org',
      url='',
      zip_safe=False,
      packages=find_packages(),

      install_requires=['matplotlib', 'json', 'scipy', 'scikit-learn', 'SoapySDR', 'numpy', 'pyrtlsdr'],

      data_files=[
      ('share/pyltesstrack/lte/', ['./lte/25-Zadoff.bin','./lte/29-Zadoff.bin','./lte/34-Zadoff.bin']),
      ],

      scripts=['pyltess-track.py']

     )
