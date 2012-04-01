#!/bin/bash

. $(dirname $0)/environment.sh

if [ ! -f $CACHEROOT/libxml2-$XML2_VERSION.tar.gz ] ; then
	try curl -L ftp://xmlsoft.org/libxml2/libxml2-$XML2_VERSION.tar.gz > $CACHEROOT/libxml2-$XML2_VERSION.tar.gz
fi
if [ ! -d $TMPROOT/libxml2-$XML2_VERSION ]; then
	try tar xzf $CACHEROOT/libxml2-$XML2_VERSION.tar.gz
	try rm -rf $TMPROOT/libxml2-$XML2_VERSION
	try mv libxml2-$XML2_VERSION $TMPROOT

fi

if [ ! -f $CACHEROOT/libxslt-$XSLT_VERSION.tar.gz ] ; then
	try curl -L ftp://xmlsoft.org/libxml2/libxslt-$XSLT_VERSION.tar.gz > $CACHEROOT/libxslt-$XSLT_VERSION.tar.gz
fi
if [ ! -d $TMPROOT/libxslt-$XSLT_VERSION ]; then
	try tar xzf $CACHEROOT/libxslt-$XSLT_VERSION.tar.gz
	try rm -rf $TMPROOT/libxslt-$XML2_VERSION
	try mv libxslt-$XSLT_VERSION $TMPROOT
fi

if [ ! -f $CACHEROOT/lxml-$LXML_VERSION.tar.gz ]; then
	try curl -L http://pypi.python.org/packages/source/l/lxml/lxml-$LXML_VERSION.tar.gz > $CACHEROOT/lxml-$LXML_VERSION.tar.gz
fi
if [ ! -d $TMPROOT/lxml-$LXML_VERSION ]; then
	try tar xzf $CACHEROOT/lxml-$LXML_VERSION.tar.gz
	try rm -rf $TMPROOT/lxml-$LXML_VERSION
	try mv lxml-$LXML_VERSION $TMPROOT
fi

# build libxml2
pushd $TMPROOT/libxml2-$XML2_VERSION
if [ ! -f .libs/libxml2.a ]; then
	try ./configure --prefix=/usr/local/iphone \
		--host=arm-apple-darwin \
		--enable-static=yes \
		--enable-shared=no \
		--without-modules \
		--without-legacy \
		--without-history \
		--without-debug \
		--without-docbook \
		--without-python \
		--without-iconv \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
	try sed -i '' 's/ runtest\$(EXEEXT) \\/ \\/' Makefile
	try sed -i '' 's/ testrecurse\$(EXEEXT)$//' Makefile
	try make clean
	try make
	try cp .libs/libxml2.a $BUILDROOT/lib/libxml2.a
	try cp -a include $BUILDROOT/include/libxml2
fi
popd

# build libxslt
pushd $TMPROOT/libxslt-$XSLT_VERSION
if [ ! -f libxslt/.libs/libxslt.a ]; then
	try ./configure --build=i686-pc-linux-gnu --host=arm-linux-eabi \
		--enable-static=yes \
		--enable-shared=no \
		--without-plugins \
		--without-debug \
		--without-python \
		--without-crypto \
		--with-libxml-src=$TMPROOT/libxml2-$XML2_VERSION \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"

	try make clean
	try make

	try cp libxslt/.libs/libxslt.a $BUILDROOT/lib/libxslt.a
	try cp libexslt/.libs/libexslt.a $BUILDROOT/lib/libexslt.a
fi
popd

# build lxml
OLD_CC="$CC"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
export CC="$ARM_CC -I$BUILDROOT/include -I$TMPROOT/libxslt-$XSLT_VERSION"
export LDFLAGS="$ARM_LDFLAGS -L$TMPROOT/libxslt-$XSLT_VERSION/libxslt/.libs"
export LDFLAGS="$LDFLAGS -L$TMPROOT/libxslt-$XSLT_VERSION/libexslt/.libs"
export LDFLAGS="$LDFLAGS -L$TMPROOT/libxml2-$XML2_VERSION/.libs"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

pushd $TMPROOT/lxml-$LXML_VERSION
HOSTPYTHON=$TMPROOT/Python-$PYTHON_VERSION/hostpython
try $HOSTPYTHON setup.py build_ext
try $HOSTPYTHON setup.py install -O2 --root iosbuild
popd

export CC="$OLD_CC"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"

bd=$TMPROOT/lxml-$LXML_VERSION/build/lib.macosx-*/lxml
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/liblxml.a $bd
deduplicate $BUILDROOT/lib/liblxml.a
