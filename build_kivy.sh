#!/bin/bash

. ./environment.sh

set -x

if [ ! -d kivy ]; then
	try git clone https://github.com/tito/kivy
	try cd kivy
	try git checkout ios-support
	try cd ..
fi

if [ "X$1" == "X-f" ]; then
	try cd kivy
	try git clean -dxf
	try git fetch
	try git checkout ios-support
	try cd ..
fi

export LDSHARED="$KIVYIOSROOT/liblink"

cd kivy
make ios

echo "Now create kivy.a archive"
# FIXME this part is build/cpu dependent :/
build_dir=build/lib.macosx-*/kivy
try $KIVYIOSROOT/biglink $build_dir $build_dir/graphics $build_dir/core/window $build_dir/core/text $build_dir/core/image
try mv kivy.a $BUILDROOT/lib
