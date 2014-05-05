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
    if [ ! -e $TMPROOT/openssl/ios-openssl/lib/libssl.a ] ; then
        echo "Binary not found. Building..."
        if [ ! -d $TMPROOT/openssl/ios-openssl/lib ] ; then
            try mkdir $TMPROOT/openssl/ios-openssl/lib
        fi
        try pushd .
        cd $TMPROOT/openssl/ios-openssl
        # Please refer to the script below for details of the OpenSSL build
        sh build.sh
        try popd
    else
        echo "Binaries found. Skipping build..."
    fi
else
    echo "Folder found. Pulling latest..."
    try pushd .
    cd $TMPROOT/openssl/ios-openssl
    git pull
    try popd 
fi

# Copy the binaries to the appropriate places.
if [ $TMPROOT/openssl/ios-openssl/lib/libssl.a ] ; then
    echo "Copying built OpenSSL binaries..."
    cp $TMPROOT/openssl/ios-openssl/lib/libssl.a $BUILDROOT/lib/libssl.a
    cp $TMPROOT/openssl/ios-openssl/lib/libcrypto.a $BUILDROOT/lib/libcrypto.a
fi
