#!/bin/bash

echo "Building libffi ============================="

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/libffi-$FFI_VERSION.tar.gz ]; then
    try curl -L ftp://sourceware.org/pub/libffi/libffi-$FFI_VERSION.tar.gz > $CACHEROOT/libffi-$FFI_VERSION.tar.gz 
fi
if [ ! -d $TMPROOT/libffi-$FFI_VERSION ]; then
    try rm -rf $TMPROOT/libffi-$FFI_VERSION
    try tar xvf $CACHEROOT/libffi-$FFI_VERSION.tar.gz
    try mv libffi-$FFI_VERSION $TMPROOT
fi

if [ -f $TMPROOT/libffi-$FFI_VERSION/build/Release-iphoneos/libffi.a ]; then
    exit 0;
fi

# lib not found, compile it
pushd $TMPROOT/libffi-$FFI_VERSION
try patch -p1 < $KIVYIOSROOT/src/ffi_files/ffi-$FFI_VERSION-sysv.S.patch

try xcodebuild -project libffi.xcodeproj -target "libffi iOS" -configuration Release -sdk iphoneos$SDKVER OTHER_CFLAGS="-no-integrated-as" SYMROOT=build

try cp build/Release-iphoneos/libffi.a $BUILDROOT/lib/libffi.a
try cp -a build/Release-iphoneos/usr/local/include $BUILDROOT/include/ffi
popd
