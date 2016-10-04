Kivy for iOS
============

This toolchain is designed to compile the necessary libraries for iOS to run
your application and manage the creation of the Xcode project.

Currently, we do not provide any binary distributions of this toolchain, but we
aim to. Until then, you do need to compile it at least once before creating
your Xcode project.

The toolchain supports:

- iPhone Simulator (x86 and x86_64)
- iPhone / iOS (armv7 and arm64)

These recipes are not ported to the new toolchain yet:

- lxml


Requirements
------------

Currently, the toolchain requires a few tools for compilation. You will need:

#. Xcode 6 or above, with an iOS SDK and command line tools installed::

    xcode-select --install

#. Using brew, you can install the following dependencies::

    brew install autoconf automake libtool pkg-config
    brew link libtool

#. Install Cython (0.23)::

    # pip method if available (sudo might be needed.)
    pip install cython==0.23


Using the toolchain
-------------------

Any Python extensions or C/C++ library must be compiled: you need to have what
we call a `recipe` to compile it. For example, Python, libffi, SDL2, SDL_image,
freetype... all the dependencies, compilation and packaging instructions are
contained in a `recipe`.

You can list the available recipes and their versions with::

    $ ./toolchain.py recipes
    freetype     2.5.5
    hostpython   2.7.1
    ios          master
    kivy         ios-poly-arch
    libffi       3.2.1
    openssl      1.0.2e
    pyobjus      master
    python       2.7.1
    sdl2         iOS-improvements
    sdl2_image   2.0.0
    sdl2_mixer   2.0.0
    sdl2_ttf     2.0.12

Then, start the compilation with::

    $ ./toolchain.py build kivy

You can build recipes at the same time by adding them as parameters::

    $ ./toolchain.py build openssl kivy

Recipe builds can be removed via the clean command e.g.::

    $ ./toolchain.py clean openssl

The Kivy recipe depends on several others, like the sdl* and python recipes.
These may in turn depend on others e.g. sdl2_ttf depends on freetype, etc.
You can think of it as follows: the kivy recipe will compile everything
necessary for a minimal working version of Kivy.

Don't grab a coffee, just do diner. Compiling all the libraries for the first
time, 4x over (remember, 4 archs, 2 per platforms), will take time. (TODO:
provide a way to not compile for the simulator.).

For a complete list of available commands, type::

    $ ./toolchain.py

Create the Xcode project
------------------------

The `toolchain.py` can create the initial Xcode project for you::

    $ ./toolchain.py create <title> <app_directory>
    $ ./toolchain.py create Touchtracer ~/code/kivy/examples/demo/touchtracer

Your app directory must contain a main.py. A directory named `<title>-ios`
will be created, with an Xcode project in it.
You can open the Xcode project using::

    $ open touchtracer-ios/touchtracer.xcodeproj

Then click on `Play`, and enjoy.

.. note::

    Everytime you press `Play`, your application directory will be synced to
    the `<title>-ios/YourApp` directory. Don't make changes in the -ios
    directory directly.

Configuring your App
--------------------

When you first build your XCode project, a 'main.m' file is created in your
XCode project folder. This file configures your environment variables and
controls your application startup. You can edit this file to customize your
launch environment.

.. note::

    If you wish to restrict your apps orientation, you should do this via
    the 'export_orientation' function in 'main.m'. The XCode orientation
    settings should be set to support all. 

FAQ
---

Fatal error: "stdio.h" file not found
    You need to install the Command line tools: `xcode-select --install`
    
You must build with bitcode disabled (Xcode setting ENABLE_BITCODE should be No).
    We don't support bitcode. You need to go to the project setting, and disable bitcode.

Support
-------

If you need assistance, you can ask for help on our mailing list:

* User Group : https://groups.google.com/group/kivy-users
* Email      : kivy-users@googlegroups.com

We also have an IRC channel:

* Server  : irc.freenode.net
* Port    : 6667, 6697 (SSL only)
* Channel : #kivy

Contributing
------------

We love pull requests and discussing novel ideas. Check out our
`contribution guide <http://kivy.org/docs/contribute.html>`_ and
feel free to improve Kivy for iOS.

The following mailing list and IRC channel are used exclusively for
discussions about developing the Kivy framework and its sister projects:

* Dev Group : https://groups.google.com/group/kivy-dev
* Email     : kivy-dev@googlegroups.com

IRC channel:

* Server  : irc.freenode.net
* Port    : 6667, 6697 (SSL only)
* Channel : #kivy-dev

License
-------

Kivy for iOS is released under the terms of the MIT License. Please refer to the
LICENSE file.
