#!/bin/bash

. $(dirname $0)/environment.sh

OLD_CC="$CC"
OLD_CFLAGS="$CFLAGS"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
export CC="$ARM_CC -I$BUILDROOT/include"
export CFLAGS="$ARM_CFLAGS"
export LDFLAGS="$ARM_LDFLAGS"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

try pushd $KIVYIOSROOT/src/ios
HOSTPYTHON=$TMPROOT/Python-$PYTHON_VERSION/hostpython
try $KIVYIOSROOT/tools/cythonize.py *.pyx
try $HOSTPYTHON setup.py build_ext
try $HOSTPYTHON setup.py install -O2 --root iosbuild
try find iosbuild | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
try rm -rdf "$BUILDROOT/python/lib/python2.7/site-packages/ios*"
try cp iosbuild/usr/local/lib/python2.7/site-packages/ios.so "$BUILDROOT/python/lib/python2.7/site-packages"
popd

export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

bd=$KIVYIOSROOT/src/ios/build/lib.macosx-*/
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libios.a $bd
deduplicate $BUILDROOT/lib/libios.a
