# FAQ for Kivy for iOS

## Introduction

Kivy for iOS (kivy-ios) is a toolchain to compile the necessary libraries for 
[iOS](https://www.apple.com/ios/) to run [Kivy](https://kivy.org) applications,
and manage the creation of [Xcode](https://developer.apple.com/xcode/) projects.

## FAQ

### Fatal error: "stdio.h" file not found

You need to install the Command line tools: `xcode-select --install`

### Error: SDK "iphonesimulator" cannot be located

Xcode path is not set up correctly. Run the following command to fix this: `sudo xcode-select --switch <YOUR_XCODEAPP_PATH>` (Change `<YOUR_XCODEAPP_PATH>` to the path that reflects your XCode installation, usually is `/Applications/Xcode.app`)

### Bitcode is partially supported now (Xcode setting ENABLE_BITCODE can be set to Yes).

* Supported recipes: python3, kivy, sdl2, sdl2_image, sdl2_mixer, and libffi

### You don't have permissions to run

It is due to invalid archs, search for them and check it. Maybe you
targetted a simulator but have only arm64. Maybe you want to target
your iPad but it is only x86_64.

### Why does the python multiprocess/subprocess module not work?

The iOS application model does not currently support multi-processing in a
cross-platform compatible way. The application design focuses on minimizing
processor usage (to minimize power consumption) and promotes an 
[alternative concurrency model](https://developer.apple.com/library/archive/documentation/General/Conceptual/ConcurrencyProgrammingGuide/Introduction/Introduction.html).

If you need to make use of multiple processes, you should consider using
[PyObjus](https://github.com/kivy/pyobjus) to leverage native iOS
functionals for this.

