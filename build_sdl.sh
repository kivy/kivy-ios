#!/bin/bash
. ./environment.sh
pushd sdl/sdl1.3/Xcode-iPhoneOS/SDL
xcodebuild -project SDLiPhoneOS.xcodeproj -target libSDL -configuration Debug -sdk iphoneos5.0
popd

#the binarie is under sdl/sdl1.3/Xcode-iPhoneOS/SDL/build/Release-Universal/
cp sdl/sdl1.3/Xcode-iPhoneOS/SDL/build/Debug-iPhoneOS/libSDL.a $BUILDROOT/lib
cp -a sdl/sdl1.3/include $BUILDROOT/include/SDL 
