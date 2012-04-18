Kivy for IOS
============

(This is a work in progress.)

#. Build the whole toolchain with `tools/build_all.sh`
#. Create an Xcode project for your application with `tools/create-xcode-project.sh test /path/to/app`
#. Open your newly created Xcode project
#. Ensure code signing is setup correctly
#. Click on play

Notes
-----

A build phase is added to the project that processes and moves your
app's files to the Xcode project before every build. If you would like
to handle this process manually, remove the "Run Script" build phase
from your target and use `tools/populate-project.sh /path/to/app`
after every change. You can also change the path to your app by modifying this build phase.
