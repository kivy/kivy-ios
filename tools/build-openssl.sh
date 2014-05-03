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
echo "About to test ..."
if [ -d $TMPROOT/openssl/ios-openssl ] ; then
    echo "ios-openssl folder found. Looking for binary..."
    if [ ! $TMPROOT/openssl/ios-openssl/lib/libssl.a ] ; then
        echo "Binary not found. Building..."
        try mkdir $TMPROOT/openssl/ios-openssl/lib
        try pushd .
        cd $TMPROOT/openssl/ios-openssl
        # Please refer to the script below for details of the OpenSSL build
        sh build.sh
        try popd
    fi
fi

# Copy the binaries to the appropriate places.
if [ $TMPROOT/openssl/ios-openssl/lib/libssl.a ] ; then
    cp $TMPROOT/openssl/ios-openssl/lib/libssl.a $BUILDROOT/lib/libssl.a
    cp $TMPROOT/openssl/ios-openssl/lib/libcrypto.a $BUILDROOT/lib/libcrypto.a
fi
