Kivy for IOS
============

This toolchain is designed to compile the necessary library for iOS to run your
application, and manage the creation of the Xcode project.

Currently, we do not provide any binary distribution of this toolchain, but we
aim to do it. So you do need to compile it at least one time before being about
to create your Xcode project.

The toolchain supports:

- iPhone Simulator (x86 and x86_64)
- iPhone / iOS (armv7 and arm64)

Theses recipes are not ported to the new toolchain yet:

- openssl
- openssl-link
- lxml


Requirements
------------

Currently, the toolchain requires few tools to let you compile. You need:

#. Xcode 6, with iOS SDK installed / command line tools.
#. Using brew, you can install dependencies::

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

You can list the available recipes and the version with::

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

Then, starts the compilation with::

    $ ./toolchain.py build kivy

The Kivy recipe depends on severals one, like all the sdl* and python. sdl2_ttf
depends on freetype, etc. You can think as: it will compile everything
necessary for a minimal working version of Kivy.

Don't grab a coffee, just do diner. Compiling all the things the first time, 4x
(remember, 4 archs, 2 per platforms), it will take time. (todo: provide a way
to not compile for the simulator.).

Create the Xcode project
------------------------

The `toolchain.py` can create for you the initial Xcode project::

    $ # ./toolchain.py create <title> <app_directory>
    $ ./toolchain.py create Touchtracer ~/code/kivy/examples/demo/touchtracer

Your app directory must contain a main.py. A directory named `<title>-ios`
will be created, with an Xcode project in it.
You can open the Xcode project::

    $ open touchtracer-ios/touchtracer.xcodeproj

Then click on `Play`, and enjoy.

.. notes::

    Everytime you press `Play`, your application directory will be synced to
    the `<title>-ios/YourApp` directory. Don't make changes in the -ios
    directory directly.

