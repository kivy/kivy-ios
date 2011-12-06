#!/bin/bash

. environment.sh

if [ ! -f $CACHEROOT/freetype-$FT_VERSION.tar.bz2 ]; then
	curl -L http://download.savannah.gnu.org/releases/freetype/freetype-$FT_VERSION.tar.bz2 > $CACHEROOT/freetype-$FT_VERSION.tar.bz2
	tar xjf $CACHEROOT/freetype-$FT_VERSION.tar.bz2
fi

if [ -f freetype-$FT_VERSION/libfreetype-arm7.a ]; then
	exit 0;
fi

# lib not found, compile it
pushd freetype-$FT_VERSION
./configure --prefix=/usr/local/iphone \
	--host=arm-apple-darwin \
	--enable-static=yes \
	--enable-shared=no \
	CC="$CCACHE $DEVROOT/usr/bin/arm-apple-darwin10-llvm-gcc-4.2" \
	AR="$DEVROOT/usr/bin/ar" \
	LDFLAGS="-isysroot $SDKROOT -miphoneos-version-min=$SDKVER" \
	CFLAGS="-march=armv7 -mcpu=arm1176jzf -mcpu=cortex-a8 -O0 -g -miphoneos-version-min=$SDKVER -isysroot $SDKROOT"
make clean
make

# copy to buildroot
cp objs/.libs/libfreetype.a $BUILDROOT/lib/libfreetype.a
cp -a include $BUILDROOT/include/freetype

popd
