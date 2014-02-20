#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -d $TMPROOT/ffmpeg-android ] ; then
	try pushd $TMPROOT
	try git clone -b ios https://github.com/tito/ffmpeg-android
	try cd ffmpeg-android
	try popd
fi

cd $TMPROOT/ffmpeg-android
if [ ! -d ffmpeg ]; then
	try ./extract.sh
fi

OLD_CC="$CC"
OLD_CFLAGS="$CFLAGS"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
export CC="$ARM_CC"
export CFLAGS="$ARM_CFLAGS"
export LDFLAGS="$ARM_LDFLAGS"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

# build ffmpeg library
try env FFMPEG_ARCHS="ios" ./build-h264-aac.sh

# build python extension
cd python
export FFMPEG_LIBRAIRES="SDL2 SDL_mixer"
export FFMPEG_LIBRARY_DIRS="$BUILDROOT/lib/lib"
export FFMPEG_INCLUDES="$BUILDROOT/include $BUILDROOT/include/SDL"
export FFMPEG_ROOT="$TMPROOT/ffmpeg-android/build/ffmpeg/armeabi-neon"

$HOSTPYTHON setup.py build_ext -v &>/dev/null
try find . -iname '*.pyx' -exec $KIVYIOSROOT/tools/cythonize.py {} \;
try $HOSTPYTHON setup.py install -O2 --root iosbuild
try find iosbuild | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
try cp -a iosbuild/usr/local/lib/python2.7/site-packages/ffmpeg "$BUILDROOT/python/lib/python2.7/site-packages"

export CC="$OLD_CC"
export CFLAGS="$OLD_CFLAGS"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

bd=$TMPROOT/ffmpeg-android/python/build/lib.macosx-*/ffmpeg
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/libffmpeg.a $bd
deduplicate $BUILDROOT/lib/libffmpeg.a

# copy ffmpeg libraries too
try cp -a $TMPROOT/ffmpeg-android/build/ffmpeg/armeabi-a8/lib/*.a $BUILDROOT/lib/
