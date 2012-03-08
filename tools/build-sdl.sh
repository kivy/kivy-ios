#!/bin/bash
. $(dirname $0)/environment.sh
pushd $KIVYIOSROOT/src/SDL/Xcode-iPhoneOS/SDL
xcodebuild -project SDLiPhoneOS.xcodeproj -target libSDL -configuration Release -sdk iphoneos5.0
popd

cp src/SDL/Xcode-iPhoneOS/SDL/build/Release-iPhoneOS/libSDL.a $BUILDROOT/lib
cp -a src/SDL/include $BUILDROOT/include/SDL 
