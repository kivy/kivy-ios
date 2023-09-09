# For OSX or Linux installation use setup_1.py. This is for use with Kivy for iOS
# Expects setup_1.py to be called previously (This creates the *.c source file for Kivy compilation)
from distutils.core import setup, Extension
# import numpy as np

setup(
    name='rotation',
    version='0.0.2',
    author='Jeremy Rittenhouse',
    author_email='jrittenhouse@diamondkinetics.com',
    description='Mirror SciPy functions that don\'t contain fortran code',
    ext_modules=[Extension('rotation',
                            ['rotation.c'])]
)
