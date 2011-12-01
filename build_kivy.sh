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

cd kivy
make ios

