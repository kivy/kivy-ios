#!/bin/bash

. environment.sh

if [ ! -f $CACHEROOT/SDL_ttf-$SDLTTF_VERSION.tar.gz ]; then
	curl -L http://www.libsdl.org/projects/SDL_ttf/release/SDL_ttf-$SDLTTF_VERSION.tar.gz > $CACHEROOT/SDL_ttf-$SDLTTF_VERSION.tar.gz
	tar xzf $CACHEROOT/SDL_ttf-$SDLTTF_VERSION.tar.gz
fi

if [ ! -f SDL_ttf-$SDLTTF_VERSION/.libs/libSDL_ttf.a ]; then
	pushd SDL_ttf-$SDLTTF_VERSION
	rm libSDL_ttf.la
	./configure --prefix=/usr/local/iphone \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no \
		--without-x \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
	make clean
	make libSDL_ttf.la
	popd
fi


# copy to buildroot
cp SDL_ttf-$SDLTTF_VERSION/.libs/libSDL_ttf.a $BUILDROOT/lib/libSDL_ttf.a
cp -a SDL_ttf-$SDLTTF_VERSION/SDL_ttf.h $BUILDROOT/include
