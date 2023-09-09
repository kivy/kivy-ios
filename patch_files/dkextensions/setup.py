# For OSX or Linux installation use setup_1.py. This is for use with Kivy for iOS
# Expects setup_1.py to be called previously (This createds the dkextensions.c source file for Kivy compilation)
from distutils.core import setup, Extension
# import numpy as np

setup(
    name='dkextensions',
    version='1.5.1',
    author='Jeremy Rittenhouse',
    author_email='jrittenhouse@diamondkinetics.com',
    description='Cythonize slowest parts of PE code',
    ext_modules=[Extension('dkextensions',
                            ['dkextensions.c'])]
)
