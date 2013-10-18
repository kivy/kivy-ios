#!/bin/bash

echo "Building pyobjus ============================="

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/pyobjus ] ; then
try pushd $TMPROOT
try git clone https://github.com/kivy/pyobjus.git
try popd
fi

try pushd $TMPROOT/pyobjus

OLD_CC="$CC"
OLD_CFLAGS="$CFLAGS"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
export CC="$ARM_CC -I$BUILDROOT/include -I$BUILDROOT/include/ffi"
export CFLAGS="$ARM_CFLAGS"
export LDFLAGS="$ARM_LDFLAGS"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

rm -rdf iosbuild/
try mkdir iosbuild

try $HOSTPYTHON setup.py build_ext
try $HOSTPYTHON setup.py install -O2 --root iosbuild

# Strip away the large stuff
find iosbuild/ | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
rm -rdf "$BUILDROOT/python/lib/python2.7/site-packages/pyobjus"
try cp -R "iosbuild/usr/local/lib/python2.7/site-packages/pyobjus" "$BUILDROOT/python/lib/python2.7/site-packages"
popd

export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

bd=$TMPROOT/pyobjus/build/lib.macosx-*/pyobjus
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libpyobjus.a $bd 
deduplicate $BUILDROOT/lib/libpyobjus.a

# copy objc bridge class -> it is used for implementing some objc methods, eg. for accelerometer
try cp $TMPROOT/pyobjus/objc_classes/aux/* $KIVYIOSROOT/tools/templates

echo "Succesufully finished building pyobjus ==================="
