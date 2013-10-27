#!/bin/bash

. $(dirname $0)/environment.sh

pushd $TMPROOT

if [ ! -f SDL ]; then
	ln -s $KIVYIOSROOT/src/SDL SDL
fi

if [ ! -d SDL_mixer ]; then
	try hg clone http://hg.libsdl.org/SDL_mixer/#SDL-1.2
fi
if [ ! -d libtremor/tremor ]; then
	try mkdir -p libtremor
	try cd libtremor
	try svn co https://svn.xiph.org/trunk/Tremor tremor
	try cd tremor
	try patch -p0 < $KIVYIOSROOT/src/tremor-configure.patch
	try cd ../..
fi
if [ ! -d libogg ]; then
	try curl -L http://downloads.xiph.org/releases/ogg/libogg-1.3.0.tar.gz > $CACHEROOT/libogg-1.3.0.tar.gz
	try tar xzf $CACHEROOT/libogg-1.3.0.tar.gz
	try mv libogg-1.3.0 libogg
fi

if [ ! -f libogg/src/.libs/libogg.a ]; then
	try cd libogg
	try ./configure --disable-shared \
		--prefix=$DESTROOT \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
	try make
	try make install
	try cd ..
fi

if [ ! -f libtremor/tremor/.libs/libvorbisidec.a ]; then
	try cd libtremor/tremor
	echo > asm_arm.h
	CC="$ARM_CC" AR="$ARM_AR" \
	LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS" \
	OGG_CFLAGS="-I../../libogg/include" \
	OGG_LDFLAGS="-L../../libogg/src/.libs" \
	PKG_CONFIG_LIBDIR="../../libogg" \
	ACLOCAL_FLAGS="-I $DESTROOT/share/aclocal -I `aclocal --print-ac-dir` -I /usr/local/share/aclocal" ./autogen.sh \
	    --prefix=$DESTROOT \
		--disable-shared \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no
	try make
	try make install
	try cd ../..
fi

popd

try cp $TMPROOT/libogg/src/.libs/libogg.a $BUILDROOT/lib
try cp $TMPROOT/libtremor/tremor/.libs/libvorbisidec.a $BUILDROOT/lib

#if [ -f $TMPROOT/SDL_mixer/libSDL_mixer-arm7.a ]; then
#	exit 0;
#fi

if [ ! -f $TMPROOT/libtremor/ogg ]; then
	ln -s $TMPROOT/libogg/include/ogg $TMPROOT/libtremor
fi

pushd $TMPROOT/SDL_mixer/Xcode-iOS
try xcodebuild $XCODEBUILD_FLAGS  -project SDL_mixer.xcodeproj 
popd

try cp $TMPROOT/SDL_mixer/Xcode-iOS/build/Release-$TARGET_SDK/libSDL_mixer.a $BUILDROOT/lib
try cp -a $TMPROOT/SDL_mixer/SDL_mixer.h $BUILDROOT/include
