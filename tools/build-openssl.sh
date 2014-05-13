#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/openssl ] ; then
    mkdir $TMPROOT/openssl
fi

# Check we have a cloned repo
if [ ! -d $TMPROOT/openssl/ios-openssl ] ; then
    echo "ios-openssl repo not found. Pulling latest..."
    try pushd .
    cd $TMPROOT/openssl
    try git clone -b master https://github.com/zen-code/ios-openssl
    try popd
fi

# Build the required binaries
if [ -d $TMPROOT/openssl/ios-openssl ] ; then
    echo "ios-openssl repo found. Building now..."
    if [ ! -d $TMPROOT/openssl/ios-openssl/lib ] ; then
        try mkdir $TMPROOT/openssl/ios-openssl/lib
    fi
    try pushd .
    cd $TMPROOT/openssl/ios-openssl
    # Please refer to the script below for details of the OpenSSL build
    sh build.sh
    try popd
fi

echo "Copying built OpenSSL binaries..."
cp $TMPROOT/openssl/ios-openssl/lib/libssl.a $BUILDROOT/lib/libssl.a
cp $TMPROOT/openssl/ios-openssl/lib/libcrypto.a $BUILDROOT/lib/libcrypto.a

sh $KIVYIOSROOT/tools/build-ssllink.sh