#!/bin/zsh

. ./environment.sh

# credit to:
# http://randomsplat.com/id5-cross-compiling-python-for-embedded-linux.html
# http://latenitesoft.blogspot.com/2008/10/iphone-programming-tips-building-unix.html

# download python and patch if they aren't there
if [[ ! -a $CACHEROOT/Python-$PYTHON_VERSION.tar.bz2 ]]; then
    curl http://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.bz2 > $CACHEROOT/Python-$PYTHON_VERSION.tar.bz2
fi

# get rid of old build
rm -rf Python-$PYTHON_VERSION
tar -xjf $CACHEROOT/Python-$PYTHON_VERSION.tar.bz2
pushd ./Python-$PYTHON_VERSION

# Patch Python for temporary reduce PY_SSIZE_T_MAX otherzise, splitting string doesnet work
try patch -p1 < ../python_files/Python-$PYTHON_VERSION-ssize-t-max.patch
try patch -p1 < ../python_files/Python-$PYTHON_VERSION-dynload.patch

# Copy our setup for modules
cp ../python_files/ModulesSetup Modules/Setup.local


echo "Building for native machine ============================================"

./configure CC="$CCACHE clang -Qunused-arguments -fcolor-diagnostics"
make python.exe Parser/pgen
mv python.exe hostpython
mv Parser/pgen Parser/hostpgen
make distclean


echo "Building for iOS ======================================================="

# patch python to cross-compile
patch -p1 < ../python_files/Python-$PYTHON_VERSION-xcompile.patch

# set up environment variables for cross compilation
export CPPFLAGS="-I$SDKROOT/usr/lib/gcc/arm-apple-darwin11/4.2.1/include/ -I$SDKROOT/usr/include/"
export CFLAGS="$CPPFLAGS -pipe -no-cpp-precomp -isysroot $SDKROOT"
export LDFLAGS="-isysroot $SDKROOT -Lextralibs/"
export CPP="$CCACHE /usr/bin/cpp $CPPFLAGS"
export CFLAGS="$CFLAGS -march=armv7 -mcpu=arm1176jzf-s -mcpu=cortex-a8"
export LDFLAGS="$LDFLAGS -march=armv7 -mcpu=arm1176jzf-s -mcpu=cortex-a8"
export MACOSX_DEPLOYMENT_TARGET=

# make a link to a differently named library for who knows what reason
mkdir extralibs||echo "foo"
ln -s "$SDKROOT/usr/lib/libgcc_s.1.dylib" extralibs/libgcc_s.10.4.dylib || echo "sdf"

try ./configure CC="$CCACHE $DEVROOT/usr/bin/arm-apple-darwin10-llvm-gcc-4.2" \
            LD="$DEVROOT/usr/bin/ld" \
		--disable-toolbox-glue \
		--host=armv7-apple-darwin \
		--prefix=/python \
	    --without-doc-strings

try make HOSTPYTHON=./hostpython HOSTPGEN=./Parser/hostpgen \
     CROSS_COMPILE_TARGET=yes

try make install HOSTPYTHON=./hostpython CROSS_COMPILE_TARGET=yes prefix="$BUILDROOT/python"

try mv -f $BUILDROOT/python/lib/libpython2.7.a $BUILDROOT/lib/
