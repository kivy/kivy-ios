#!/bin/bash
. ./environment.sh
pushd sdl/sdl1.3/Xcode-iPhoneOS/SDL
xcodebuild -project SDLiPhoneOS.xcodeproj -target libSDL -configuration Debug -sdk iphoneos5.0
popd

cp sdl/sdl1.3/Xcode-iPhoneOS/SDL/build/Release-iPhoneOS/libSDL.a $BUILDROOT/lib
cp -a sdl/sdl1.3/include $BUILDROOT/include/SDL 
