from distutils.core import setup, Extension
import os

setup(name='ios',
      version='1.0',
      ext_modules=[
        Extension(
            'ios', ['ios.c', 'ios_mail.m', 'ios_browser.m'],
            libraries=[ ],
            library_dirs=[],
            )
        ]
      )
