#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/freetype-$FT_VERSION.tar.bz2 ]; then
	try curl -L http://download.savannah.gnu.org/releases/freetype/freetype-$FT_VERSION.tar.bz2 > $CACHEROOT/freetype-$FT_VERSION.tar.bz2
	try tar xjf $CACHEROOT/freetype-$FT_VERSION.tar.bz2
	try mv freetype-$FT_VERSION $TMPROOT
fi

if [ -f $TMPROOT/freetype-$FT_VERSION/libfreetype-arm7.a ]; then
	exit 0;
fi

# lib not found, compile it
pushd $TMPROOT/freetype-$FT_VERSION
try ./configure --prefix=/usr/local/iphone \
	--host=arm-apple-darwin \
	--enable-static=yes \
	--enable-shared=no \
	CC="$ARM_CC" AR="$ARM_AR" \
	LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
try make clean
try make

# copy to buildroot
cp objs/.libs/libfreetype.a $BUILDROOT/lib/libfreetype.a
cp -a include $BUILDROOT/include/freetype

popd
