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

PREFIX=$TMPROOT/lxmlinstall
if [ ! -d $PREFIX ]; then
	try mkdir $PREFIX
fi

# build libxml2
pushd $TMPROOT/libxml2-$XML2_VERSION
if [ ! -f .libs/libxml2.a ]; then
	try ./configure \
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
		--prefix=$PREFIX \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"
	try sed -i '' 's/ runtest\$(EXEEXT) \\/ \\/' Makefile
	try sed -i '' 's/ testrecurse\$(EXEEXT)$//' Makefile
	try make clean install
	try make
	try make install
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
		--prefix=$PREFIX \
		CC="$ARM_CC" AR="$ARM_AR" \
		LDFLAGS="$ARM_LDFLAGS" CFLAGS="$ARM_CFLAGS"

	try make clean
	try make
	try make install

	try cp libxslt/.libs/libxslt.a $BUILDROOT/lib/libxslt.a
	try cp libexslt/.libs/libexslt.a $BUILDROOT/lib/libexslt.a
fi
popd

# build lxml
OLD_CC="$CC"
OLD_LDFLAGS="$LDFLAGS"
OLD_LDSHARED="$LDSHARED"
OLD_PATH="$PATH"
export PATH="$PREFIX/bin:$PATH"
export CC="$ARM_CC -I$PREFIX/include"
export LDFLAGS="$ARM_LDFLAGS -L$PREFIX/lib"
export LDSHARED="$KIVYIOSROOT/tools/liblink"

pushd $TMPROOT/lxml-$LXML_VERSION
XML2_CONFIG=$PREFIX/bin/xml2-config
XSLT_CONFIG=$PREFIX/bin/xslt-config

#pushd src
#find . -name *.pyx -exec $KIVYIOSROOT/tools/cythonize.py {} \;
#popd
find . -name *.pyx -exec $CYTHON {} \;

try $HOSTPYTHON setup.py build_ext 
try $HOSTPYTHON setup.py install -O2 --root iosbuild

find iosbuild/ | grep -E '*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
rm -rdf "$BUILDROOT/python/lib/python2.7/site-packages/lxml"
try cp -R "iosbuild/usr/local/lib/python2.7/site-packages/lxml" "$BUILDROOT/python/lib/python2.7/site-packages"

popd

export CC="$OLD_CC"
export LDFLAGS="$OLD_LDFLAGS"
export LDSHARED="$OLD_LDSHARED"
export PATH="$OLD_PATH"

bd=$TMPROOT/lxml-$LXML_VERSION/build/lib.macosx-*/lxml
try $KIVYIOSROOT/tools/biglink $BUILDROOT/lib/liblxml.a $bd
deduplicate $BUILDROOT/lib/liblxml.a
