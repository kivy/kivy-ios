#!/bin/bash

. $(dirname $0)/environment.sh

echo "Building libjpeg...."

if [ ! -f $CACHEROOT/jpegsrc.v6b.tar.gz ]; then
	try curl -L http://downloads.sourceforge.net/project/libjpeg/libjpeg/6b/jpegsrc.v6b.tar.gz > $CACHEROOT/jpegsrc.v6b.tar.gz
fi
if [ ! -d $TMPROOT/jpeg-6b ]; then
        rm -rf $CACHEROOT/jpeg-6b 
	try tar -xvf $CACHEROOT/jpegsrc.v6b.tar.gz
	try mv jpeg-6b $TMPROOT
fi

# lib not found, compile it
echo "Configuring...."
pushd $TMPROOT/jpeg-6b
try ./configure --prefix=$DESTROOT \
	--host=arm-apple-darwin \
	--enable-static=yes \
	--enable-shared=no \
	CC="$ARM_CC" AR="$ARM_AR" \
	LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
patch < $KIVYIOSROOT/src/jpeg_files/jpeg_makefile.patch
try make clean
make #With controlled errors

rm *.a
rm cjpeg.o
rm djpeg.o
rm jpegtran.o
rm rdjpgcom.o
rm urjpgcom.o
rm rdjtran.o
rm wrjpgcom.o 
ar rcs libjpeg.a *.o 


# copy to buildroot
cp libjpeg.a $BUILDROOT/lib/libjpeg.a
cp *.h $BUILDROOT/include/

popd
