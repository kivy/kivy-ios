#!/bin/bash

try () {
	"$@" || exit -1
}

# iOS SDK Environmnent
SDKVER=5.0
DEVROOT=/Developer/Platforms/iPhoneOS.platform/Developer
SDKROOT=$DEVROOT/SDKs/iPhoneOS$SDKVER.sdk

# version of packages
PYTHON_VERSION=2.7.1

# where the build will be located
ROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export BUILDROOT="$ROOT/build"
export CACHEROOT="$ROOT/.cache"

# for external project
export KIVYIOSROOT="$ROOT"

# some tools
CCACHE=$(which ccache)

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
