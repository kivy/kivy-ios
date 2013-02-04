#!/bin/bash

if [ "X$VERBOSE" == "X1" ]; then
	set -x
fi

try () {
	"$@" || exit -1
}

# iOS SDK Environmnent
export SDKVER=`xcodebuild -showsdks | fgrep "iphoneos" | tail -n 1 | awk '{print $2}'`
export DEVROOT=`xcode-select -print-path`/Platforms/iPhoneOS.platform/Developer
export SDKROOT=$DEVROOT/SDKs/iPhoneOS$SDKVER.sdk

if [ ! -d $DEVROOT ]; then
	echo "Unable to found the Xcode iPhoneOS.platform"
	echo
	echo "The path is automatically set from 'xcode-select -print-path'"
	echo " + /Platforms/iPhoneOS.platform/Developer"
	echo
	echo "Ensure 'xcode-select -print-path' is set."
	exit 1
fi

# iOS SDK Environmnent for the simulator
export SIMULATOR_SDKVER=`xcodebuild -showsdks | fgrep "iphonesimulator" | tail -n 1 | awk '{print $2}'`
export SIMULATOR_DEVROOT=`xcode-select -print-path`/Platforms/iPhoneSimulator.platform/Developer
export SIMULATOR_SDKROOT=$SIMULATOR_DEVROOT/SDKs/iPhoneSimulator$SDKVER.sdk

if [ ! -d $SIMULATOR_DEVROOT ]; then
	echo "Unable to found the Xcode iPhoneSimulator.platform"
	echo
	echo "The path is automatically set from 'xcode-select -print-path'"
	echo " + /Platforms/iPhoneSimulator.platform/Developer"
	echo
	echo "Ensure 'xcode-select -print-path' is set."
	exit 1
fi

# version of packages
export PYTHON_VERSION=2.7.1
export SDLTTF_VERSION=2.0.10
export FT_VERSION=2.4.8
export XML2_VERSION=2.7.8
export XSLT_VERSION=1.1.26
export LXML_VERSION=2.3.1

# where the build will be located
export KIVYIOSROOT=$PWD
export BUILDROOT="$KIVYIOSROOT/build"
export TMPROOT="$KIVYIOSROOT/tmp"
export DESTROOT="$KIVYIOSROOT/tmp/root"
export CACHEROOT="$KIVYIOSROOT/.cache"

# pkg-config for SDL and futures
try mkdir -p $BUILDROOT/pkgconfig
export PKG_CONFIG_PATH="$BUILDROOT/pkgconfig:$PKG_CONFIG_PATH"

# some tools
export CCACHE=$(which ccache)

# flags for arm (device) compilation
export ARM_CC="$CCACHE $DEVROOT/usr/bin/arm-apple-darwin10-llvm-gcc-4.2"
export ARM_AR="$DEVROOT/usr/bin/ar"
export ARM_LD="$DEVROOT/usr/bin/ld"
export ARM_CFLAGS="-march=armv7 -mcpu=arm176jzf -mcpu=cortex-a8"
export ARM_CFLAGS="$ARM_CFLAGS -pipe -no-cpp-precomp"
export ARM_CFLAGS="$ARM_CFLAGS -isysroot $SDKROOT"
export ARM_CFLAGS="$ARM_CFLAGS -miphoneos-version-min=$SDKVER"
export ARM_LDFLAGS="-isysroot $SDKROOT"
export ARM_LDFLAGS="$ARM_LDFLAGS -miphoneos-version-min=$SDKVER"

# uncomment this line if you want debugging stuff
export ARM_CFLAGS="$ARM_CFLAGS -O3"
#export ARM_CFLAGS="$ARM_CFLAGS -O0 -g"

# flags for i386 (simulator) compilation
export i386_CC="$CCACHE $SIMULATOR_DEVROOT/usr/bin/i686-apple-darwin11-llvm-gcc-4.2"
export i386_AR="$SIMULATOR_DEVROOT/usr/bin/ar"
export i386_LD="$SIMULATOR_DEVROOT/usr/bin/ld"
export i386_CFLAGS="-isysroot $SIMULATOR_SDKROOT"
export i386_LDFLAGS="-isysroot $SIMULATOR_SDKROOT"

# uncomment this line if you want debugging stuff
export i386_CFLAGS="$i386_CFLAGS -O3"
#export i386_CFLAGS="$i386_CFLAGS -O0 -g"

# create build directory if not found
try mkdir -p $BUILDROOT
try mkdir -p $BUILDROOT/include
try mkdir -p $BUILDROOT/lib
try mkdir -p $CACHEROOT
try mkdir -p $TMPROOT
try mkdir -p $DESTROOT

# one method to deduplicate some symbol in libraries
function deduplicate() {
	fn=$(basename $1)
	echo "== Trying to remove duplicate symbol in $1"
	try mkdir ddp
	try cd ddp
	try ar x $1
	try ar rc $fn *.o
	try ranlib $fn
	try mv -f $fn $1
	try cd ..
	try rm -rf ddp
}
