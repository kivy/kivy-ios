#!/bin/bash

if [ "X$VERBOSE" == "X1" ]; then
	set -x
fi

try () {
	"$@" || exit -1
}


# version of packages
export IOS_PYTHON_VERSION=2.7.1
export SDLTTF_VERSION=2.0.10
export FT_VERSION=2.4.8
export XML2_VERSION=2.7.8
export XSLT_VERSION=1.1.26
export LXML_VERSION=2.3.1
export FFI_VERSION=3.0.13

# Xcode doesn't include /usr/local/bin
export PATH="$PATH":/usr/local/bin

# ensure byte-compiling is working
export PYTHONDONTWRITEBYTECODE=




# set TARGET_SDK to iphonos by default if not specified
if [ "X$TARGET_SDK" == "X" ]; then
        export TARGET_SDK="iphoneos"
fi

#set architechuture based on which target we compiling for
export CPU_ARCHITECHTURE="armv7"
if [ "X$TARGET_SDK" == "Xiphonesimulator" ]; then
        export CPU_ARCHITECHTURE="i386"
fi

# where our built is located
export KIVYIOSROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"
export BUILDROOT="$KIVYIOSROOT/build"
export TMPROOT="$KIVYIOSROOT/tmp"
export DESTROOT="$KIVYIOSROOT/tmp/root"
export CACHEROOT="$KIVYIOSROOT/.cache"

# iOS SDK Environmnent (don't use name "SDKROOT"!!! it will break the compilation)
export SDKVER=`xcrun --sdk $TARGET_SDK --show-sdk-version`
export IOSSDKROOT=`xcrun --sdk $TARGET_SDK --show-sdk-path`



#find the right compiler and linker
export ARM_CC=$(xcrun -find -sdk $TARGET_SDK clang)
export ARM_AR=$(xcrun -find -sdk $TARGET_SDK ar)
export ARM_LD=$(xcrun -find -sdk $TARGET_SDK ld)

# flags for arm compilation 
# (not really arm if building for simlator...but it's all the stuff we're cross comiling for iOS)
export ARM_CFLAGS="-arch $CPU_ARCHITECHTURE"
export ARM_CFLAGS="$ARM_CFLAGS -pipe -no-cpp-precomp"
export ARM_CFLAGS="$ARM_CFLAGS -isysroot $IOSSDKROOT"
export ARM_CFLAGS="$ARM_CFLAGS -miphoneos-version-min=$SDKVER"


# flags for linker
export ARM_LDFLAGS="-arch $CPU_ARCHITECHTURE -isysroot $IOSSDKROOT"
export ARM_LDFLAGS="$ARM_LDFLAGS -miphoneos-version-min=$SDKVER"

# uncomment this line if you want debugging stuff
export ARM_CFLAGS="$ARM_CFLAGS -O3"
#export ARM_CFLAGS="$ARM_CFLAGS -O0 -g"

#general xcode build settings
export XCODEBUILD_FLAGS="ONLY_ACTIVE_ARCH=NO ARCHS=$CPU_ARCHITECHTURE -configuration Release -sdk ${TARGET_SDK} --arch=$CPU_ARCHITECHTURE"




##CHECK sanity of configuration
if [ ! -d $IOSSDKROOT ]; then
        echo "Unable to found the target $TARGET_SDK SDK "
	echo
	echo "The path is automatically set from 'xcrun --sdk $TARGET_SDK --show-sdk-path'" 
	exit 1
fi


# some tools
export CCACHE=$(which ccache)
export HOSTPYTHON="$TMPROOT/Python-$IOS_PYTHON_VERSION/hostpython"
for fn in cython-2.7 cython; do
	export CYTHON=$(which $fn)
	if [ "X$CYTHON" != "X" ]; then
		break
	fi
done
if [ "X$CYTHON" == "X" ]; then
	echo
	echo "Cython not found !"
	echo "Ensure your PATH contain access to 'cython' or 'cython-2.7'"
	echo
	echo "Current PATH: $PATH"
	echo
fi

# check basic tools
CONFIGURATION_OK=1
for tool in pkg-config autoconf automake libtool hg; do
	if [ "X$(which $tool)" == "X" ]; then
		echo "Missing requirement: $tool is not installed !"
		CONFIGURATION_OK=0
	fi
done
if [ $CONFIGURATION_OK -eq 0 ]; then
	echo "Install thoses requirements first, then restart the script."
	exit 1
fi


#now do some setup...

# pkg-config for SDL and futures
try mkdir -p $BUILDROOT/pkgconfig
export PKG_CONFIG_PATH="$BUILDROOT/pkgconfig:$PKG_CONFIG_PATH"


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
