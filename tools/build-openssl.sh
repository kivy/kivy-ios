#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/openssl ] ; then
    mkdir $TMPROOT/openssl
fi

if [ ! -d $TMPROOT/openssl/ios-openssl ] ; then
    try pushd $TMPROOT/openssl
    try git clone -b master https://github.com/zen-code/ios-openssl
    cd $TMPROOT/openssl/ios-openssl
    build.sh
    try popd
fi

# copy to buildroot
#cp $TMPROOT/SDL_ttf-$SDLTTF_VERSION/.libs/libSDL_ttf.a $BUILDROOT/lib/libSDL_ttf.a
#cp -a $TMPROOT/SDL_ttf-$SDLTTF_VERSION/SDL_ttf.h $BUILDROOT/include
