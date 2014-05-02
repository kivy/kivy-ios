#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/openssl ] ; then
    mkdir $TMPROOT/openssl
fi

# Check we have a cloned repo
if [ ! -d $TMPROOT/openssl/ios-openssl ] ; then
    try pushd .
    cd $TMPROOT/openssl
    try git clone -b master https://github.com/zen-code/ios-openssl
    try popd
fi

# Build the required binaries
if [ -d $TMPROOT/openssl/ios-openssl ] ; then
    try pushd .
    cd $TMPROOT/openssl/ios-openssl
    sh build.sh
    try popd
fi

# copy to buildroot
#cp $TMPROOT/SDL_ttf-$SDLTTF_VERSION/.libs/libSDL_ttf.a $BUILDROOT/lib/libSDL_ttf.a
#cp -a $TMPROOT/SDL_ttf-$SDLTTF_VERSION/SDL_ttf.h $BUILDROOT/include
