#!/bin/bash

. environment.sh

if [ ! -d kivy ] ; then
	try git clone https://github.com/kivy/kivy
	try cd kivy
	try git checkout ios-support
	try cd ..
fi

if [ "X$1" = "X-f" ] ; then
	try cd kivy
	try git clean -dxf
	try git fetch
	try git checkout ios-support
	try cd ..
fi

cd kivy
export LDSHARED="$KIVYIOSROOT/liblink"
export CFLAGS="$ARM_CFLAGS"
make ios

# FIXME this part is build/cpu dependent :/
bd=build/lib.macosx-*/kivy
try $KIVYIOSROOT/biglink $BUILDROOT/lib/libkivy.a $bd $bd/graphics $bd/core/window $bd/core/text $bd/core/image
deduplicate $BUILDROOT/lib/libkivy.a
