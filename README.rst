Kivy for IOS
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

- openssl
- openssl-link
- lxml


Requirements
------------

Currently, the toolchain requires a few tools for compilation. You will need:

#. Xcode 6 or above, with an iOS SDK and command line tools installed::

    xcode-select --install

#. Using brew, you can install the following dependencies::

    brew install autoconf automake libtool pkg-config
    brew link libtool

#. Install Cython (0.21)::

    # pip method if available (sudo might be needed.)
    pip install cython==0.21


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
    pyobjus      master
    python       2.7.1
    sdl2         iOS-improvements
    sdl2_image   2.0.0
    sdl2_mixer   2.0.0
    sdl2_ttf     2.0.12

Then, start the compilation with::

    $ ./toolchain.py build kivy

The Kivy recipe depends on several others, like the sdl* and python recipes.
These may in turn depend on others e.g. sdl2_ttf depends on freetype, etc.
You can think of it as follows: the kivy recipe will compile everything
necessary for a minimal working version of Kivy.

Don't grab a coffee, just do diner. Compiling all the libraries for the first
time, 4x over (remember, 4 archs, 2 per platforms), will take time. (TODO:
provide a way to not compile for the simulator.).

Create the Xcode project
------------------------

The `toolchain.py` can create the initial Xcode project for you::

    $ # ./toolchain.py create <title> <app_directory>
    $ ./toolchain.py create Touchtracer ~/code/kivy/examples/demo/touchtracer

Your app directory must contain a main.py. A directory named `<title>-ios`
will be created, with an Xcode project in it.
You can open the Xcode project using::

    $ open touchtracer-ios/touchtracer.xcodeproj

Then click on `Play`, and enjoy.

.. notes::

    Everytime you press `Play`, your application directory will be synced to
    the `<title>-ios/YourApp` directory. Don't make changes in the -ios
    directory directly.

FAQ
---

Fatal error: "stdio.h" file not found
    You need to install the Command line tools: `xcode-select --install`
