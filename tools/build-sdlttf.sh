#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/SDL_ttf-$SDLTTF_VERSION.tar.gz ]; then
	try curl -L http://www.libsdl.org/projects/SDL_ttf/release/SDL_ttf-$SDLTTF_VERSION.tar.gz > $CACHEROOT/SDL_ttf-$SDLTTF_VERSION.tar.gz
fi
if [ ! -d $TMPROOT/SDL_ttf-$SDLTTF_VERSION ]; then
	try rm -rf $TMPROOT/SDL_ttf-$SDLTTF_VERSION
	try tar xzf $CACHEROOT/SDL_ttf-$SDLTTF_VERSION.tar.gz
	try mv SDL_ttf-$SDLTTF_VERSION $TMPROOT
	try pushd $TMPROOT/SDL_ttf-$SDLTTF_VERSION
	try patch -p1 < $KIVYIOSROOT/tools/patches/SDL_ttf-colorkey.patch
	popd
fi

if [ ! -f $TMPROOT/SDL_ttf-$SDLTTF_VERSION/.libs/libSDL_ttf.a ]; then
	pushd $TMPROOT/SDL_ttf-$SDLTTF_VERSION
	rm libSDL_ttf.la

	# generate a sdl.pc file that contain all the information of our generated SDL
	try ./configure --prefix=/usr/local/iphone \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no \
		--without-x \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
	try make clean
	try make libSDL_ttf.la
	popd
fi


# copy to buildroot
cp $TMPROOT/SDL_ttf-$SDLTTF_VERSION/.libs/libSDL_ttf.a $BUILDROOT/lib/libSDL_ttf.a
cp -a $TMPROOT/SDL_ttf-$SDLTTF_VERSION/SDL_ttf.h $BUILDROOT/include
