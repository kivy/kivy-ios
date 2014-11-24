#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/numpy-$NUMPY_VERSION.tar.gz ] ; then
	try curl -L http://pypi.python.org/packages/source/n/numpy/numpy-$NUMPY_VERSION.tar.gz > $CACHEROOT/numpy-$NUMPY_VERSION.tar.gz
fi
if [ ! -d $TMPROOT/numpy-$NUMPY_VERSION ]; then
	cd $TMPROOT
	try tar -xvf $CACHEROOT/numpy-$NUMPY_VERSION.tar.gz
	try cd numpy-$NUMPY_VERSION
	try patch -p1 < $KIVYIOSROOT/src/numpy-$NUMPY_VERSION.patch
	try cd ../..
fi

# Save current flags
OLD_CC="$CC"
OLD_CFLAGS="$CFLAGS"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
export CC="$ARM_CC -I$BUILDROOT/include"
export CFLAGS="$ARM_CFLAGS"
export LDFLAGS="$ARM_LDFLAGS"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

# CC must have the CFLAGS with arm arch, because numpy tries first to compile
# and execute an empty C to see if the compiler works. This is obviously not
# working when crosscompiling
export CC="$ARM_CC $CFLAGS"

# Numpy configuration. Don't try to compile anything related to it, we're
# going to use the Accelerate framework
NPYCONFIG="env BLAS=None LAPACK=None ATLAS=None"

try pushd $TMPROOT/numpy-$NUMPY_VERSION
try $NPYCONFIG $HOSTPYTHON setup.py build_ext -v
try $NPYCONFIG $HOSTPYTHON setup.py install -O2 --root iosbuild
try find iosbuild | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/core/include
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/core/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/distutils
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/doc
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/f2py/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/fft/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/lib/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/ma/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/matrixlib/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/polynomial/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/random/tests
try rm -rf iosbuild/usr/local/lib/python2.7/site-packages/numpy/tests
if [ -d "$BUILDROOT/python/lib/python2.7/site-packages/numpy" ]; then
	rm -rf $BUILDROOT/python/lib/python2.7/site-packages
fi
try cp -a iosbuild/usr/local/lib/python2.7/site-packages/numpy "$BUILDROOT/python/lib/python2.7/site-packages/"
popd

# Restore the old compilation flags
export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

# Create the static library
bd=$TMPROOT/numpy-$NUMPY_VERSION/build/lib.macosx-*/numpy
rm -f $BUILDROOT/lib/libnumpy.a
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libnumpy.a \
	$bd/core $bd/lib $bd/fft $bd/linalg $bd/random
deduplicate \
	$BUILDROOT/lib/libnumpy.a \
    $TMPROOT/numpy-$NUMPY_VERSION/build/temp.macosx-*/libnpymath.a \
    $TMPROOT/numpy-$NUMPY_VERSION/build/temp.macosx-*/libnpysort.a
