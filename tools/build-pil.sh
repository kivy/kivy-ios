#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/Imaging-1.1.7.tar.gz ] ; then
	try curl -L http://effbot.org/downloads/Imaging-1.1.7.tar.gz > $CACHEROOT/Imaging-1.1.7.tar.gz
fi
if [ ! -d $TMPROOT/Imaging-1.1.7 ]; then
	cd $TMPROOT
	try tar -xvf $CACHEROOT/Imaging-1.1.7.tar.gz
fi



# build audiostream
OLD_CC="$CC"
OLD_CFLAGS="$CFLAGS"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
export CC="$ARM_CC -I$BUILDROOT/include"
export CFLAGS="$ARM_CFLAGS"
export LDFLAGS="$ARM_LDFLAGS"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

try pushd $TMPROOT/Imaging-1.1.7
patch -p1 < $KIVYIOSROOT/src/pil_files/patch_pil.patch
$HOSTPYTHON setup.py build_ext &>/dev/null
try find . -iname '*.pyx' -exec $KIVYIOSROOT/tools/cythonize.py {} \;
try $HOSTPYTHON setup.py build_ext
try $HOSTPYTHON setup.py install -O2 --root iosbuild
try find iosbuild | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
try cp -a iosbuild/usr/local/lib/python2.7/site-packages/PIL "$BUILDROOT/python/lib/python2.7/site-packages"
popd

export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

bd=$TMPROOT/Imaging-1.1.7/build/lib.macosx-*
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libpil.a $bd 
deduplicate $BUILDROOT/lib/libpil.a
