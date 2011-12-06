#!/bin/bash

. environment.sh

try ./build_python.sh
try ./reduce_python.sh
try ./build_sdl.sh
try ./build_freetype.sh
try ./build_sdlttf.sh
try ./build_kivy.sh

echo '== Build done'
echo "Available libraries in $BUILDROOT/lib"
echo $(ls $BUILDROOT/lib)
