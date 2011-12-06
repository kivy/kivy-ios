#!/bin/bash

. environment.sh

SDLTTF_VERSION=2.0.10

if [ ! -d SDL_ttf-$SDLTTF_VERSION ]; then
	curl -L http://www.libsdl.org/projects/SDL_ttf/release/SDL_ttf-$SDLTTF_VERSION.tar.gz > SDL_ttf-$SDLTTF_VERSION.tar.gz
	tar xzf SDL_ttf-$SDLTTF_VERSION.tar.gz
fi

if [ -f SDL_ttf-$SDLTTF_VERSION/libSDL_ttf-arm7.a ]; then
	exit 0;
fi


cd SDL_ttf-$SDLTTF_VERSION
rm libSDL_ttf.la
./configure --prefix=/usr/local/iphone --host=arm-apple-darwin \
	--enable-static=yes --enable-shared=no \
	--without-x \
	CC=$DEVROOT/usr/bin/arm-apple-darwin10-llvm-gcc-4.2 AR=$DEVROOT/usr/bin/ar LDFLAGS="-isysroot $SDKROOT -miphoneos-version-min=$SDKVER" CFLAGS="-march=armv7 -mcpu=arm1176jzf -mcpu=cortex-a8 -O0 -g -miphoneos-version-min=$SDKVER -isysroot $SDKROOT"
make clean
make libSDL_ttf.la

# copy to buildroot
cp .libs/libSDL_ttf.a $BUILDROOT/lib/libSDL_ttf.a
cp -a SDL_ttf.h $BUILDROOT/include
