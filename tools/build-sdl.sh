#!/bin/bash
. $(dirname $0)/environment.sh
pushd $KIVYIOSROOT/src/SDL/Xcode-iOS/SDL
xcodebuild -project SDL.xcodeproj -target libSDL -configuration Release -sdk iphoneos$SDKVER
popd

cp src/SDL/Xcode-iOS/SDL/build/Release-iphoneos/libSDL.a $BUILDROOT/lib
cp -a src/SDL/include $BUILDROOT/include/SDL 
