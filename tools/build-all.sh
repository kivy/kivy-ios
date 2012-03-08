#!/bin/bash

. $(dirname $0)/environment.sh

try $(dirname $0)/build-python.sh
try $(dirname $0)/reduce-python.sh
try $(dirname $0)/build-sdl.sh
try $(dirname $0)/build-freetype.sh
try $(dirname $0)/build-sdlttf.sh
try $(dirname $0)/build-sdlmixer.sh
try $(dirname $0)/build-kivy.sh

echo '== Build done'
echo "Available libraries in $BUILDROOT/lib"
echo $(ls $BUILDROOT/lib)
