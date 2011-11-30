#!/bin/bash

set -x

SDLTTF_VERSION=2.0.10
SDKVER=5.0
DEVROOT=/Developer/Platforms/iPhoneOS.platform/Developer
SDKROOT=$DEVROOT/SDKs/iPhoneOS$SDKVER.sdk

if [ ! -d SDL_ttf-$SDLTTF_VERSION ]; then
	curl -L http://www.libsdl.org/projects/SDL_ttf/release/SDL_ttf-$SDLTTF_VERSION.tar.gz > SDL_ttf-$SDLTTF_VERSION.tar.gz
	tar xzf SDL_ttf-$SDLTTF_VERSION.tar.gz
fi

if [ -f SDL_ttf-$SDLTTF_VERSION/libSDL_ttf-arm7.a ]; then
	exit 0;
fi


cd SDL_ttf-2.0.10
rm libSDL_ttf.la
./configure --prefix=/usr/local/iphone --host=arm-apple-darwin \
	--enable-static=yes --enable-shared=no \
	--without-x \
	CC=$DEVROOT/usr/bin/arm-apple-darwin10-llvm-gcc-4.2 AR=$DEVROOT/usr/bin/ar LDFLAGS="-isysroot $SDKROOT -miphoneos-version-min=$SDKVER" CFLAGS="-pipe -mdynamic-no-pic -std=c99 -Wno-trigraphs -fpascal-strings -O2 -Wreturn-type -Wunused-variable -fmessage-length=0 -fvisibility=hidden -miphoneos-version-min=$SDKVER -isysroot $SDKROOT"
make clean
make libSDL_ttf.la
cp .libs/libSDL_ttf.a libSDL_ttf-arm7.a
