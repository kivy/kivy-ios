# Kivy for iOS

[![Backers on Open Collective](https://opencollective.com/kivy/backers/badge.svg)](#backers)
[![Sponsors on Open Collective](https://opencollective.com/kivy/sponsors/badge.svg)](#sponsors)

This toolchain is designed to compile the necessary libraries for iOS to run
your application and manage the creation of the Xcode project.

We do not provide any binary distributions of this toolchain.
You do need to compile it at least once before creating your Xcode project.

The toolchain supports:

- iPhone Simulator (x86_64)
- iPhone / iOS (armv7 and arm64)

You can select between Python 2.7 or Python 3.7 by specifying the recipes
`python2` or `python3` when building.

These recipes are not ported to the new toolchain yet:

- lxml


## Requirements

Currently, the toolchain requires a few tools for compilation. You will need:

- Ensure you have python3 installed - this is needed for toolchain.py:

      brew install python

- Ensure you have the right dependencies installed for python3:

      pip3 install -r requirements.txt

- Xcode 10 or above, with an iOS SDK and command line tools installed:

      xcode-select --install

- Using brew, you can install the following dependencies:

      brew install autoconf automake libtool pkg-config
      brew link libtool

- Install Cython (0.28.1):

      # pip method if available (sudo might be needed.)
      pip3 install cython==0.28.1


## Using the toolchain

Any Python extensions or C/C++ library must be compiled: you need to have what
we call a `recipe` to compile it. For example, Python, libffi, SDL2, SDL_image,
freetype... all the dependencies, compilation and packaging instructions are
contained in a `recipe`.

You can list the available recipes and their versions with:

    $ python3 toolchain.py recipes
    audiostream  master
    click        master
    cymunk       master
    distribute   0.7.3
    ffmpeg       2.6.3
    ffpyplayer   v3.2
    flask        master
    freetype     2.5.5
    hostlibffi   3.2.1
    hostpython2  2.7.1
    hostpython3  3.7.1
    ios          master
    itsdangerous master
    jinja2       master
    kivy         1.10.1
    libffi       3.2.1
    libjpeg      v9a
    libpng       1.6.26
    markupsafe   master
    moodstocks   4.1.5
    numpy        1.16.4
    openssl      1.0.2k
    photolibrary master
    pil          2.8.2
    pillow       6.1.0
    plyer        master
    pycrypto     2.6.1
    pykka        1.2.1
    pyobjus      master
    python2      2.7.1
    python3      3.7.1
    pyyaml       3.11
    sdl2         2.0.8
    sdl2_image   2.0.0
    sdl2_mixer   2.0.0
    sdl2_ttf     2.0.12
    werkzeug     master

Then, start the compilation with:

    $ python3 toolchain.py build python3 kivy

You can build recipes at the same time by adding them as parameters:

    $ python3 toolchain.py build python3 openssl kivy

Recipe builds can be removed via the clean command e.g.:

    $ python3 toolchain.py clean openssl
    
You can install package that don't require compilation with pip::

    $ python3 toolchain.py pip install plyer

The Kivy recipe depends on several others, like the sdl* and python recipes.
These may in turn depend on others e.g. sdl2_ttf depends on freetype, etc.
You can think of it as follows: the kivy recipe will compile everything
necessary for a minimal working version of Kivy.

Don't grab a coffee, just do diner. Compiling all the libraries for the first
time, 3x over (remember, 3 archs, x86_64, armv7, arm64) will take time.

For a complete list of available commands, type:

    $ python3 toolchain.py

## Create the Xcode project

The `toolchain.py` can create the initial Xcode project for you::

    $ python3 toolchain.py create <title> <app_directory>
    $ python3 toolchain.py create Touchtracer ~/code/kivy/examples/demo/touchtracer

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
   architectures, namely x86_64, armv7 and arm64 as per the guidelines from
   Apple. You can reduce the size of your ipa significantly by removing the
   x86_64 architecture as they are used only for the emulator.

   The procedure is to first compile/build all the host recipes as is:

      python3 toolchain.py build hostpython3

   Then build all the rest of the recipes using --arch=armv7 --arch=arm64
   arguments as follows:

      python3 toolchain.py build python3 kivy --arch=armv7 --arch=arm64

   Note that these packages will not run in the iOS emulators, so use them
   only for deployment.

## Usage

```
python3 toolchain.py <command> [<args>]

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

## FAQ

### Fatal error: "stdio.h" file not found

You need to install the Command line tools: `xcode-select --install`

### You must build with bitcode disabled (Xcode setting ENABLE_BITCODE should be No).

We don't support bitcode. You need to go to the project setting, and disable bitcode.

### You don't have permissions to run

It is due to invalid archs, search for them and check it. Maybe you
targetted a simulator but have only armv7/arm64. Maybe you want to target
your iPad but it as only x86_64.


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
