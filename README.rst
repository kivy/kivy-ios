Kivy for IOS
============

(This is a work in progress.)

#. Using brew, you can install dependencies::

    brew install autoconf automake libtool pkg-config mercurial
    brew link libtool
    brew link mercurial

#. Install Cython::

    # easy-install method
    sudo easy_install cython

    # pip method if available (sudo might be needed.)
    pip install cython

#. Build the whole toolchain with `tools/build-all.sh`
#. Create an Xcode project for your application with `tools/create-xcode-project.sh test /path/to/app`
#. Open your newly created Xcode project
#. Ensure code signing is setup correctly
#. Click on play
#. To revise your code and update the app, use `tools/populate-project.sh test /path/to/app`

Notes
-----

A build phase is added to the project that processes and moves your
app's files to the Xcode project before every build. If you would like
to handle this process manually, remove the "Run Script" build phase
from your target and use `tools/populate-project.sh /path/to/app`
after every change. You can also change the path to your app by modifying this build phase.
