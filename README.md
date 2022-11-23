# Kivy for iOS

[![kivy-ios](https://github.com/kivy/kivy-ios/workflows/kivy-ios/badge.svg)](https://github.com/kivy/kivy-ios/actions?query=workflow%3Akivy-ios)
[![PyPI version](https://badge.fury.io/py/kivy-ios.svg)](https://badge.fury.io/py/kivy-ios)
[![Backers on Open Collective](https://opencollective.com/kivy/backers/badge.svg)](#backers)
[![Sponsors on Open Collective](https://opencollective.com/kivy/sponsors/badge.svg)](#sponsors)

This toolchain is designed to compile the necessary libraries for iOS to run
your application and manage the creation of the Xcode project.

We do not provide any binary distributions of this toolchain.
You do need to compile it at least once before creating your Xcode project.

The toolchain supports:

- iPhone Simulator (x86_64)
- iPhone / iOS (arm64)

These recipes are not ported to the new toolchain yet:

- lxml


## Installation & requirements

Before we start, we strongly advise to use a Python virtual environment to install Python packages.

      python3 -m venv venv
      . venv/bin/activate

Install [Kivy for iOS from PyPI](https://pypi.org/project/kivy-ios) with pip like any Python package.

      pip3 install kivy-ios

Additionally you would need few system dependencies and configuration.

- Xcode 10 or above, with an iOS SDK and command line tools installed:

      xcode-select --install

- Using brew, you can install the following dependencies:

      brew install autoconf automake libtool pkg-config
      brew link libtool

## Using the toolchain

Any Python extensions or C/C++ library must be compiled: you need to have what
we call a `recipe` to compile it. For example, Python, libffi, SDL2, SDL_image,
freetype... all the dependencies, compilation and packaging instructions are
contained in a `recipe`.

You can list the available recipes and their versions with:

    $ toolchain recipes
    audiostream  master
    click        7.1.2
    cymunk       master
    ffmpeg       n4.3.1
    ffpyplayer   v3.2
    flask        1.1.2
    freetype     2.5.5
    hostlibffi   3.2.1
    hostopenssl  1.1.1g
    hostpython3  3.7.1
    ios          master
    itsdangerous 1.1.0
    jinja2       2.11.2
    kivy         1.10.1
    libffi       3.2.1
    libjpeg      v9a
    libpng       1.6.26
    markupsafe   1.1.1
    moodstocks   4.1.5
    numpy        1.16.4
    openssl      1.1.1g
    photolibrary master
    pillow       6.1.0
    plyer        master
    pycrypto     2.6.1
    pykka        1.2.1
    pyobjus      master
    python3      3.7.1
    pyyaml       3.11
    sdl2         2.0.8
    sdl2_image   2.0.0
    sdl2_mixer   2.0.0
    sdl2_ttf     2.0.12
    werkzeug     1.0.1

Then, start the compilation with:

    $ toolchain build python3 kivy

You can build recipes at the same time by adding them as parameters:

    $ toolchain build python3 openssl kivy

Recipe builds can be removed via the clean command e.g.:

    $ toolchain clean openssl

You can install package that don't require compilation with pip::

    $ toolchain pip install plyer

The Kivy recipe depends on several others, like the sdl\* and python recipes.
These may in turn depend on others e.g. sdl2_ttf depends on freetype, etc.
You can think of it as follows: the kivy recipe will compile everything
necessary for a minimal working version of Kivy.

Don't grab a coffee, just do dinner. Compiling all the libraries for the first
time, 2x over (remember, 2 archs, x86_64, arm64) will take time.

For a complete list of available commands, type:

    $ toolchain

## Create the Xcode project

The `toolchain.py` can create the initial Xcode project for you::

    $ toolchain create <title> <app_directory>
    $ toolchain create Touchtracer ~/code/kivy/examples/demo/touchtracer

Your app directory must contain a main.py. A directory named `<title>-ios`
will be created, with an Xcode project in it.
You can open the Xcode project using::

    $ open touchtracer-ios/touchtracer.xcodeproj

Then click on `Play`, and enjoy.

> *Did you know ?*
>
> Everytime you press `Play`, your application directory will be synced to
> the `<title>-ios/YourApp` directory. Don't make changes in the -ios
> directory directly.


## Configuring your App

You can configure and customize your app in various ways:

- Set the icon and launch images in XCode. Note that XCode requires that you
   specify these assests per device or/and iOS version.

- When you first build your XCode project, a 'main.m' file is created in your
   XCode project folder. This file configures your environment variables and
   controls your application startup. You can edit this file to customize your
   launch environment.

- Kivy uses SDL, and as soon as the application starts the SDL main, the launch
   image will disappear. To prevent that, you need to have 2 files named
   `Default.png` and `Default-Landscape.png`, and put them
   in the `Resources` folder in Xcode (not in your application folder)

> *Did you know ?*
>
> If you wish to restrict your apps orientation, you should do this via
> the 'export_orientation' function in 'main.m'. The XCode orientation
> settings should be set to support all.


## Using recipes

Recipes are used to install and compile any libraries you may need to use. These
recipes follow the same format as those used by the
[Python-for-Android](https://github.com/kivy/python-for-android) sister project.
Please refer to the
[recipe documentation](https://python-for-android.readthedocs.io/en/latest/recipes/)
there for more detail.


## Reducing the application size

If you would like to reduce the size of your distributed app, there are a few
things you can do to achieve this:

- Minimize the `build/pythonX/lib/pythonXX.zip`: this contains all the python
   modules. You can edit the zip file and remove all the files you'll not use
   (reduce encodings, remove xml, email...)

- Go to the settings `panel` > `build`, search for `"strip"` options, and
   triple-check that they are all set to `NO`. Stripping does not work with
   Python dynamic modules and will remove needed symbols.

- By default, the iOS package compiles binaries for all processor
   architectures, namely x86_64 and arm64 as per the guidelines from
   Apple. You can reduce the size of your ipa significantly by removing the
   x86_64 architecture as they are used only for the emulator.

   The procedure is to first compile/build all the host recipes as is:

      toolchain build hostpython3

   Then build all the rest of the recipes using --arch=arm64
   arguments as follows:

      toolchain build python3 kivy --arch=arm64

   Note that these packages will not run in the iOS emulators, so use them
   only for deployment.

## Usage

```
toolchain <command> [<args>]

Available commands:
    build         Build a recipe (compile a library for the required target
                    architecture)
    clean         Clean the build of the specified recipe
    distclean     Clean the build and the result
    recipes       List all the available recipes
    status        List all the recipes and their build status

Xcode:
    create        Create a new xcode project
    update        Update an existing xcode project (frameworks, libraries..)
    launchimage   Create Launch images for your xcode project
    icon          Create Icons for your xcode project
    pip           Install a pip dependency into the distribution
    pip3          Install a pip dependency into the python 3 distribution
```

## Development

Alternatively, it's also possible to clone the repository and use all the
described commands in the above sections.
Clone and install it to your local virtual environment:

    git clone https://github.com/kivy/kivy-ios.git
    cd kivy-ios/
    python3 -m venv venv
    . venv/bin/activate
    pip install -e .

Then use the `toolchain.py` script:

    python toolchain.py --help


## FAQ

### Fatal error: "stdio.h" file not found

You need to install the Command line tools: `xcode-select --install`

### Error: SDK "iphonesimulator" cannot be located

Xcode path is not set up correctly. Run the following command to fix this: `sudo xcode-select --switch <YOUR_XCODEAPP_PATH>` (Change `<YOUR_XCODEAPP_PATH>` to the path that reflects your XCode installation, usually is `/Applications/Xcode.app`)

### Bitcode is partially supported now (Xcode setting ENABLE_BITCODE can be set to Yes).

* Supported recipes: python3, kivy, sdl2, sdl2_image, sdl2_mixer and libffi

### You don't have permissions to run

It is due to invalid archs, search for them and check it. Maybe you
targetted a simulator but have only arm64. Maybe you want to target
your iPad but it as only x86_64.

### Why does the python multiprocess/subprocess module not work?

The iOS application model does not currently support multi-processing in a
cross-platform compatible way. The application design focuses on minimizing
processor usage (to minimize power consumption) and promotes an
[alternative concurrency model](https://developer.apple.com/library/archive/documentation/General/Conceptual/ConcurrencyProgrammingGuide/Introduction/Introduction.html).

If you need to make use of multiple processes, you should consider using
[PyObjus](https://github.com/kivy/pyobjus) to leverage native iOS
functionals for this.

## Support

If you need assistance, you can ask for help on our mailing list:

* User Group : https://groups.google.com/group/kivy-users
* Email      : kivy-users@googlegroups.com

We also have a Discord channel:

* Server     : https://chat.kivy.org
* Channel    : #support


## Contributing

We love pull requests and discussing novel ideas. Check out our
[contribution guide](http://kivy.org/docs/contribute.html) and
feel free to improve Kivy for iOS.

The following mailing list and IRC channel are used exclusively for
discussions about developing the Kivy framework and its sister projects:

* Dev Group : https://groups.google.com/group/kivy-dev
* Email     : kivy-dev@googlegroups.com

Discord channel:

* Server     : https://chat.kivy.org
* Channel    : #dev

## License

Kivy for iOS is released under the terms of the MIT License. Please refer to the
LICENSE file.


## Backers

Thank you to all our backers! 🙏 [[Become a backer](https://opencollective.com/kivy#backer)]

<a href="https://opencollective.com/kivy#backers" target="_blank"><img src="https://opencollective.com/kivy/backers.svg?width=890"></a>


## Sponsors

Support this project by becoming a sponsor. Your logo will show up here with a link to your website. [[Become a sponsor](https://opencollective.com/kivy#sponsor)]

<a href="https://opencollective.com/kivy/sponsor/0/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/1/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/2/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/3/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/4/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/5/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/6/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/7/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/8/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/9/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/9/avatar.svg"></a>
