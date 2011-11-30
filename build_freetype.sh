#!/bin/bash

set -x

FT_VERSION=2.4.8
SDKVER=5.0
DEVROOT=/Developer/Platforms/iPhoneOS.platform/Developer
SDKROOT=$DEVROOT/SDKs/iPhoneOS$SDKVER.sdk

if [ ! -d freetype-$FT_VERSION ]; then
	curl -L http://download.savannah.gnu.org/releases/freetype/freetype-$FT_VERSION.tar.bz2 > freetype-$FT_VERSION.tar.bz2
	tar xjf freetype-$FT_VERSION.tar.bz2
fi

if [ -f freetype-$FT_VERSION/libfreetype-arm7.a ]; then
	exit 0;
fi

# lib not found, compile it
pushd .
cd freetype-$FT_VERSION
./configure --prefix=/usr/local/iphone --host=arm-apple-darwin --enable-static=yes --enable-shared=no CC=$DEVROOT/usr/bin/arm-apple-darwin10-llvm-gcc-4.2 AR=$DEVROOT/usr/bin/ar LDFLAGS="-isysroot $SDKROOT -miphoneos-version-min=$SDKVER" CFLAGS="-pipe -mdynamic-no-pic -std=c99 -Wno-trigraphs -fpascal-strings -O2 -Wreturn-type -Wunused-variable -fmessage-length=0 -fvisibility=hidden -miphoneos-version-min=$SDKVER -isysroot $SDKROOT"
make clean
make
cp objs/.libs/libfreetype.a libfreetype-arm7.a

