#!/bin/bash

try () {
	"$@" || exit -1
}

# iOS SDK Environmnent
SDKVER=5.0
DEVROOT=/Developer/Platforms/iPhoneOS.platform/Developer
SDKROOT=$DEVROOT/SDKs/iPhoneOS$SDKVER.sdk

# where the build will be located
ROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILDROOT="$ROOT/build"

# for external project
export KIVYIOSROOT="$ROOT"

# create build directory if not found
set -x
if [ ! -d $BUILDROOT ]; then
	try mkdir $BUILDROOT
	try mkdir $BUILDROOT/include
	try mkdir $BUILDROOT/lib
fi
