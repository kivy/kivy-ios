#!/bin/bash

echo "Building plyer ============================="

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/plyer ] ; then
try pushd $TMPROOT
try git clone https://github.com/kivy/plyer.git
try popd
fi

try pushd $TMPROOT/plyer

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

try $HOSTPYTHON setup.py build
try $HOSTPYTHON setup.py install -O2 --root iosbuild

# Strip away the large stuff
find iosbuild/ | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm

# Remove other platforms except ios
iosbuild_path="iosbuild/usr/local/lib/python2.7/site-packages/plyer"
find $iosbuild_path/platforms -mindepth 1 -maxdepth 1 -d -type d ! -iname ios |  xargs rm -r

rm -rdf "$BUILDROOT/python/lib/python2.7/site-packages/plyer"
try cp -R $iosbuild_path "$BUILDROOT/python/lib/python2.7/site-packages"
popd

export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

echo "Succesufully finished building plyer ==================="
