# Kivy for iOS


[![Backers on Open Collective](https://opencollective.com/kivy/backers/badge.svg)](https://opencollective.com/kivy)
[![Sponsors on Open Collective](https://opencollective.com/kivy/sponsors/badge.svg)](https://opencollective.com/kivy)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)

![PyPI - Version](https://img.shields.io/pypi/v/kivy-ios)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kivy-ios)

[![kivy-ios](https://github.com/kivy/kivy-ios/actions/workflows/kivy_ios.yml/badge.svg)](https://github.com/kivy/kivy-ios/actions/workflows/kivy_ios.yml)

Kivy for iOS (kivy-ios) is a toolchain to compile the necessary libraries for 
[iOS](https://www.apple.com/ios/) to run [Kivy](https://kivy.org) applications,
and manage the creation of [Xcode](https://developer.apple.com/xcode/) projects.

The toolchain supports:

- iPhone / iOS (arm64)
- iPhone Simulator (x86_64, arm64)

We do not provide any binary distributions of this toolchain.
You do need to compile it at least once before creating your Xcode project.

Because Xcode only runs on macOS, Kivy for iOS is only useful on this
platform.

Kivy for iOS is managed by the [Kivy Team](https://kivy.org/about.html) and can be
used with [Buildozer](https://github.com/kivy/buildozer).

## Installation & requirements

Before we start, we strongly advise using a Python virtual environment to install Python packages.

      python3 -m venv venv
      . venv/bin/activate

Install [Kivy for iOS from PyPI](https://pypi.org/project/kivy-ios) with pip like any Python package.

      pip3 install kivy-ios

Additionally, you would need a few system dependencies and configuration.

- Xcode 13 or above, with an iOS SDK and command line tools installed:

      xcode-select --install

- Using brew, you can install the following dependencies:

      brew install autoconf automake libtool pkg-config
      brew link libtool

## Using the toolchain

Any Python extensions or C/C++ library must be compiled: you need to have what
we call a `recipe` to compile it. For example, Python, libffi, SDL2, SDL_image,
freetype... all the dependencies, compilation, and packaging instructions are
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

Note: These recipes are not ported to the new toolchain yet:

- lxml

Then, start the compilation with:

    $ toolchain build python3 kivy

You can build recipes at the same time by adding them as parameters:

    $ toolchain build python3 openssl kivy

Recipe builds can be removed via the clean command e.g.:

    $ toolchain clean openssl

You can install package that don't require compilation with pip::

    $ toolchain pip install plyer

The Kivy recipe depends on several others, like the sdl\* and python recipes.
These may, in turn, depend on others e.g. sdl2_ttf depends on freetype, etc.
You can think of it as follows: the kivy recipe will compile everything
necessary for a minimal working version of Kivy.

Don't just grab a coffee; do dinner. Compiling all the libraries for the first
time, twice over (Remember: two platforms - iOS, iPhoneSimulator) will take time.

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

> *Did you know?*
>
> Every time you press `Play`, your application directory will be synced to
> the `<title>-ios/YourApp` directory. Don't make changes in the -ios
> directory directly.


## Configuring your App

You can configure and customize your app in various ways:

- Set the icon and launch images in XCode. Note that XCode requires that you
   specify these assets per device or/and iOS version.

- When you first build your XCode project, a 'main.m' file is created in your
   XCode project folder. This file configures your environment variables and
   controls your application startup. You can edit this file to customize your
   launch environment.

- Kivy uses SDL, and as soon as the application starts the SDL main, the launch
   image will disappear. To prevent that, you need to have 2 files named
   `Default.png` and `Default-Landscape.png` and put them
   in the `Resources` folder in Xcode (not in your application folder)

> *Did you know?*
>
> If you wish to restrict your app's orientation, you should do this via
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

For troubleshooting advice and other frequently asked questions, consult
the latest 
[Kivy for iOS FAQ](https://github.com/kivy/kivy-ios/blob/master/FAQ.md).

## License

Kivy for iOS is [MIT licensed](LICENSE), actively developed by a great
community and is supported by many projects managed by the 
[Kivy Organization](https://www.kivy.org/about.html).

## Support

Are you having trouble using kivy-ios or any of its related projects in the Kivy
ecosystem?
Is there an error you don’t understand? Are you trying to figure out how to use 
it? We have volunteers who can help!

The best channels to contact us for support are listed in the latest 
[Contact Us](https://github.com/kivy/kivy-ios/blob/master/CONTACT.md) document.

## Contributing

kivy-ios is part of the [Kivy](https://kivy.org) ecosystem - a large group of
products used by many thousands of developers for free, but it
is built entirely by the contributions of volunteers. We welcome (and rely on) 
users who want to give back to the community by contributing to the project.

Contributions can come in many forms. See the latest 
[Contribution Guidelines](https://github.com/kivy/kivy-ios/blob/master/CONTRIBUTING.md)
for how you can help us.

## Code of Conduct

In the interest of fostering an open and welcoming community, we as 
contributors and maintainers need to ensure participation in our project and 
our sister projects is a harassment-free and positive experience for everyone. 
It is vital that all interaction is conducted in a manner conveying respect, 
open-mindedness and gratitude.

Please consult the [latest Kivy Code of Conduct](https://github.com/kivy/kivy/blob/master/CODE_OF_CONDUCT.md).

## Contributors

This project exists thanks to 
[all the people who contribute](https://github.com/kivy/kivy-ios/graphs/contributors).
[[Become a contributor](CONTRIBUTING.md)].

<img src="https://contrib.nn.ci/api?repo=kivy/python-for-android&pages=5&no_bot=true&radius=22&cols=18">

## Backers

Thank you to [all of our backers](https://opencollective.com/kivy)! 
🙏 [[Become a backer](https://opencollective.com/kivy#backer)]

<img src="https://opencollective.com/kivy/backers.svg?width=890&avatarHeight=44&button=false">

## Sponsors

Special thanks to 
[all of our sponsors, past and present](https://opencollective.com/kivy).
Support this project by 
[[becoming a sponsor](https://opencollective.com/kivy#sponsor)].

Here are our top current sponsors. Please click through to see their websites,
and support them as they support us. 

<!--- See https://github.com/orgs/kivy/discussions/15 for explanation of this code. -->
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
<a href="https://opencollective.com/kivy/sponsor/10/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/10/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/11/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/11/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/12/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/12/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/13/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/13/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/14/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/14/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/15/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/15/avatar.svg"></a>
