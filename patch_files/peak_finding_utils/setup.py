# Typical setup.py file. Setup.py is for use with Kivy to get working on iOS.
from distutils.core import setup, Extension
# import numpy as np

setup(
    name='peak_finding_utils',
    version='0.0.5',
    author='Jeremy Rittenhouse',
    author_email='jrittenhouse@diamondkinetics.com',
    description='Mirror SciPy functions that don\'t contain fortran code',
    ext_modules=[Extension('peak_finding_utils',
                            ['_peak_finding_utils.c'])]
)
