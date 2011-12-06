#!/bin/bash

try () {
	"$@" || exit -1
}

# iOS SDK Environmnent
export SDKVER=5.0
export DEVROOT=/Developer/Platforms/iPhoneOS.platform/Developer
export SDKROOT=$DEVROOT/SDKs/iPhoneOS$SDKVER.sdk

# version of packages
export PYTHON_VERSION=2.7.1
export SDLTTF_VERSION=2.0.10
export FT_VERSION=2.4.8

# where the build will be located
export KIVYIOSROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export BUILDROOT="$KIVYIOSROOT/build"
export CACHEROOT="$KIVYIOSROOT/.cache"

# some tools
export CCACHE=$(which ccache)

# create build directory if not found
set -x
if [ ! -d $BUILDROOT ]; then
	try mkdir -p $BUILDROOT
	try mkdir -p $BUILDROOT/include
	try mkdir -p $BUILDROOT/lib
fi

if [ ! -d $CACHEROOT ]; then
	try mkdir -p $CACHEROOT
fi
