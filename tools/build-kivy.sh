#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/kivy ] ; then
	try pushd $TMPROOT
	try git clone https://github.com/kivy/kivy
	try cd kivy
	try git checkout ios-support
	try popd
fi

if [ "X$1" = "X-f" ] ; then
	try pushd $TMPROOT/kivy
	try git clean -dxf
	try git fetch
	try git checkout ios-support
	try popd
fi

pushd $TMPROOT/kivy
export LDSHARED="$KIVYIOSROOT/tools/liblink"
export CFLAGS="$ARM_CFLAGS"
make ios
popd

# FIXME this part is build/cpu dependent :/
bd=$TMPROOT/kivy/build/lib.macosx-*/kivy
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libkivy.a $bd $bd/graphics $bd/core/window $bd/core/text $bd/core/image $bd/core/audio
deduplicate $BUILDROOT/lib/libkivy.a
