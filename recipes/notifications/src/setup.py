from distutils.core import setup, Extension
import os

setup(name='notifications',
	version='1.0',
	ext_modules=[
		Extension(
			'notifications', ['notifications.c', 'ios_notif.m'],
			libraries=[],
			library_dirs=[],
		)
	]
)
