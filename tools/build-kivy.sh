#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/kivy ] ; then
	try pushd $TMPROOT
	try git clone https://github.com/kivy/kivy
	try cd kivy
	try popd
fi

if [ "X$1" = "X-f" ] ; then
	try pushd $TMPROOT/kivy
	try git clean -dxf
	try git pull origin master
	try popd
fi

pushd $TMPROOT/kivy
OLD_CFLAGS="$CFLAGS"
OLD_LDSHARED="$LDSHARED"
export LDSHARED="$KIVYIOSROOT/tools/liblink"
export CFLAGS="$ARM_CFLAGS"

ln -s $KIVYIOSROOT/Python-$IOS_PYTHON_VERSION/python
ln -s $KIVYIOSROOT/Python-$IOS_PYTHON_VERSION/python.exe

rm -rdf iosbuild/
try mkdir iosbuild

echo "First build ========================================"
HOSTPYTHON=$TMPROOT/Python-$IOS_PYTHON_VERSION/hostpython
$HOSTPYTHON setup.py build_ext -g
echo "cythoning =========================================="
find . -name *.pyx -exec $KIVYIOSROOT/tools/cythonize.py {} \;
echo "Second build ======================================="
try $HOSTPYTHON setup.py build_ext -g
try $HOSTPYTHON setup.py install -O2 --root iosbuild
# Strip away the large stuff
find iosbuild/ | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
rm -rdf "$BUILDROOT/python/lib/python2.7/site-packages/kivy"
# Copy to python for iOS installation
try cp -R "iosbuild/usr/local/lib/python2.7/site-packages/kivy" "$BUILDROOT/python/lib/python2.7/site-packages"

export LDSHARED="$OLD_LDSHARED"
export CFLAGS="$OLD_CFLAGS"
popd

# FIXME this part is build/cpu dependent :/
bd=$TMPROOT/kivy/build/lib.macosx-*/kivy
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libkivy.a $bd $bd/graphics $bd/core/window $bd/core/text $bd/core/image $bd/core/audio
deduplicate $BUILDROOT/lib/libkivy.a
