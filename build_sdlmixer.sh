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
if [ ! -d libogg ]; then
	curl -L http://downloads.xiph.org/releases/ogg/libogg-1.3.0.tar.gz > .cache/libogg-1.3.0.tar.gz
	tar xzf .cache/libogg-1.3.0.tar.gz
	mv libogg-1.3.0 libogg
fi

if [ ! -f libogg/src/.libs/libogg.a ]; then
	cd libogg
	./configure --disable-shared \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
	make
	cd ..
fi

if [ ! -f libtremor/tremor/.libs/libvorbisidec.a ]; then
	cd libtremor/tremor
	echo > asm_arm.h
	CC="$ARM_CC" AR="$ARM_AR" \
	LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS" \
	ACLOCAL_FLAGS="-I /usr/local/share/aclocal" ./autogen.sh \
		--disable-shared \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no \
		--with-ogg-includes=../../libogg/include
	make
	cd ../..
fi

cp libogg/src/.libs/libogg.a $BUILDROOT/lib
cp libtremor/tremor/.libs/libvorbisidec.a $BUILDROOT/lib

if [ -f SDL_mixer/libSDL_mixer-arm7.a ]; then
	exit 0;
fi

pushd SDL_mixer/Xcode-iOS
xcodebuild -project SDL_mixer.xcodeproj -configuration Release
popd

cp SDL_mixer/Xcode-iOS/build/Release-iphoneos/libSDL_mixer.a $BUILDROOT/lib
cp -a SDL_mixer/SDL_mixer.h $BUILDROOT/include
