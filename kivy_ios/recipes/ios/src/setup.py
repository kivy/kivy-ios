from distutils.core import setup, Extension


setup(name='ios',
      version='1.1',
      ext_modules=[
          Extension('ios',
                    ['ios.c', 'ios_utils.m', 'ios_mail.m', 'ios_browser.m',
                     'ios_filechooser.m'],
                    libraries=[],
                    library_dirs=[],
                    )
                  ]
      )
