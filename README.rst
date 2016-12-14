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
time, 4x over (remember, 4 archs, 2 per platforms by default) will take time.

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

You can configure and customize your app in various ways:

#. Set the icon and launch images in XCode. Note that XCode requires that you
   specify these assests per device or/and iOS version.

#. When you first build your XCode project, a 'main.m' file is created in your
   XCode project folder. This file configures your environment variables and
   controls your application startup. You can edit this file to customize your
   launch environment.

#. Kivy uses SDL, and as soon as the application starts the SDL main, the launch
   image will disappear. To prevent that, you need to have 2 files named
   `Default.png` and `Default-Landscape.png`, and put them
   in the `Resources` folder in Xcode (not in your application folder)

.. note::

    If you wish to restrict your apps orientation, you should do this via
    the 'export_orientation' function in 'main.m'. The XCode orientation
    settings should be set to support all.

Using recipes
-------------

Recipes are used to install and compile any libraries you may need to use. These
recipes follow the same format as those used by the
`Python-for-Android <https://github.com/kivy/python-for-android>`_ sister project.
Please refer to the
`recipe documentation <https://python-for-android.readthedocs.io/en/latest/recipes/>`_
there for more detail.

Reducing the application size
-----------------------------

If you would like to reduce the size of your distributed app, there are a few
things you can do to achieve this:

#. Minimize the `build/python/lib/python27.zip`: this contains all the python
   modules. You can edit the zip file and remove all the files you'll not use
   (reduce encodings, remove xml, email...)

#. Go to the settings panel > build, search for "strip" options, and
   triple-check that they are all set to NO. Stripping does not work with
   Python dynamic modules and will remove needed symbols.

#. By default, the iOS package compiles binaries for all processor
   architectures, namely x86, x86_64, armv7 and arm64 as per the guidelines from
   Apple. You can reduce the size of your ipa significantly by removing the
   x86 and x86_64 architectures as they are usually used only for the emulator.

   The procedure is to first compile/build all the host recipes as is::

       ./toolchain.py build hostpython

   Then build all the rest of the recipes using --arch=armv7 --arch=arm64
   arguments as follows::

       ./toolchain.py build kivy --arch=armv7 --arch=arm64

   Note that these packages will not run in the iOS emulators, so use them
   only for deployment.

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
