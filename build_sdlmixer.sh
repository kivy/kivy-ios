#!/bin/bash

. environment.sh

if [ ! -d SDL_mixer ]; then
	hg clone http://hg.libsdl.org/SDL_mixer/
fi
if [ ! -d libtremor ]; then
	mkdir libtremor
	cd libtremor
	svn co http://svn.xiph.org/trunk/Tremor tremor
	cd ..
fi

if [ -f SDL_mixer/libSDL_mixer-arm7.a ]; then
	exit 0;
fi

pushd SDL_mixer/Xcode-iOS
xcodebuild -project SDL_mixer.xcodeproj -configuration Debug
popd

cp SDL_mixer/Xcode-iOS/build/Debug-iphoneos/libSDL_mixer.a $BUILDROOT/lib
cp -a SDL_mixer/SDL_mixer.h $BUILDROOT/include
