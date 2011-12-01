#!/bin/bash
. ./environmnent.sh
pushd sdl/sdl1.3/Xcode-iPhoneOS/SDL
xcodebuild -project SDLiPhoneOS.xcodeproj -alltargets
popd
#the binarie is under sdl/sdl1.3/Xcode-iPhoneOS/SDL/build/Release-Universal/
cp sdl/sdl1.3/Xcode-iPhoneOS/SDL/build/Release-iPhoneOS/libSDL.a $BUILDROOT/lib
cp -a sdl/sdl1.3/include $BUILDROOT/include/SDL 
