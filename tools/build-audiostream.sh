#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/audiostream-master.zip ] ; then
	try curl -L https://github.com/kivy/audiostream/archive/master.zip > $CACHEROOT/audiostream-master.zip
fi
if [ ! -d $TMPROOT/audiostream-master ]; then
	cd $TMPROOT
	try unzip $CACHEROOT/audiostream-master.zip
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

try pushd $TMPROOT/audiostream-master
HOSTPYTHON=$TMPROOT/Python-$PYTHON_VERSION/hostpython
$HOSTPYTHON setup.py build_ext &>/dev/null
try find . -iname '*.pyx' -exec $KIVYIOSROOT/tools/cythonize.py {} \;
try $HOSTPYTHON setup.py build_ext
try $HOSTPYTHON setup.py install -O2 --root iosbuild
try find iosbuild | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
try cp -a iosbuild/usr/local/lib/python2.7/site-packages/audiostream "$BUILDROOT/python/lib/python2.7/site-packages"
popd

export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

bd=$TMPROOT/audiostream-master/build/lib.macosx-*/audiostream
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libaudiostream.a $bd $bd/platform $bd/sources
deduplicate $BUILDROOT/lib/libaudiostream.a
