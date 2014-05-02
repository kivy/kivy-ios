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
if [ $TMPROOT/openssl/ios-openssl ] ; then
    if [ ! $TMPROOT/openssl/ios-openssl/lib/libssl.a ] ; then
        try mkdir $TMPROOT/openssl/ios-openssl/lib
        try pushd .
        cd $TMPROOT/openssl/ios-openssl
        sh build.sh
        try popd
    fi
fi

# Copy the binaries to the appropriate places.
if [ $TMPROOT/openssl/ios-openssl/lib/libssl.a ] ; then
    cp $TMPROOT/openssl/ios-openssl/lib/libssl.a $BUILDROOT/lib/libssl.a
    cp $TMPROOT/openssl/ios-openssl/lib/libcrypto.a $BUILDROOT/lib/libcrypto.a
fi
