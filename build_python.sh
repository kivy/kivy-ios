#!/bin/zsh

. ./environment.sh

set -o errexit
set -x

echo "Starting =========="

# credit to:
# http://randomsplat.com/id5-cross-compiling-python-for-embedded-linux.html
# http://latenitesoft.blogspot.com/2008/10/iphone-programming-tips-building-unix.html

export IOS_VERSION="5.0"
PATH_SIMU=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}-simulator
PATH_DEV=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}-device
PATH_ALL=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}

# download python and patch if they aren't there
if [[ ! -a Python-2.7.1.tar.bz2 ]]; then
    curl http://www.python.org/ftp/python/2.7.1/Python-2.7.1.tar.bz2 > python_files/Python-2.7.1.tar.bz2
fi

# get rid of old build
rm -rf Python-2.7.1
rm -rf $PATH_SIMU
rm -rf $PATH_DEV
rm -rf $PATH_ALL
if [[ -a libpython2.7-iOS5.a ]]; then
   rm -fr libpython2.7-iOS5.a
fi
tar -xjf python_files/Python-2.7.1.tar.bz2
pushd ./Python-2.7.1

# Patch Python for temporary reduce PY_SSIZE_T_MAX otherzise, splitting string doesnet work
patch -p1 < ../python_files/Python-2.7.1-ssize-t-max.patch

echo "Building for native machine ============================================"
# Compile some stuff statically; Modules/Setup taken from pgs4a-kivy
cp ../python_files/ModulesSetup Modules/Setup.local

#CC=clang ./configure
./configure CC="clang -Qunused-arguments -fcolor-diagnostics"

make python.exe Parser/pgen
#make python Parser/pgen

mv python.exe hostpython
#mv python hostpython
mv Parser/pgen Parser/hostpgen

make distclean

# patch python to cross-compile
patch -p1 < ../python_files/Python-2.7.1-xcompile.patch

# avoid iphone builddd
#if [ "X" == "C" ]; then
	echo "Building for iPhone Simulator ==========================================="
	export MACOSX_DEPLOYMENT_TARGET=10.6
	# set up environment variables for simulator compilation
	export DEVROOT="/Developer/Platforms/iPhoneSimulator.platform/Developer"
	export SDKROOT="$DEVROOT/SDKs/iPhoneSimulator${IOS_VERSION}.sdk"

	if [ ! -d "$DEVROOT" ]; then
	    echo "DEVROOT doesn't exist. DEVROOT=$DEVROOT"
	    exit 1
	fi

	if [ ! -d "$SDKROOT" ]; then
	    echo "SDKROOT doesn't exist. SDKROOT=$SDKROOT"
	    exit 1
	fi

	export CPPFLAGS="-I$SDKROOT/usr/lib/gcc/arm-apple-darwin11/4.2.1/include/ -I$SDKROOT/usr/include/"
	export CFLAGS="$CPPFLAGS -pipe -no-cpp-precomp -isysroot $SDKROOT"
	export LDFLAGS="-isysroot $SDKROOT"
	export CPP="/usr/bin/cpp $CPPFLAGS"

	# Compile some stuff statically; Modules/Setup taken from pgs4a-kivy
	cp ../python_files/ModulesSetup Modules/Setup.local

	./configure CC="$DEVROOT/usr/bin/i686-apple-darwin11-llvm-gcc-4.2 -m32" \
		    LD="$DEVROOT/usr/bin/ld" --disable-toolbox-glue --host=i386-apple-darwin --prefix=/python

	make HOSTPYTHON=./hostpython HOSTPGEN=./Parser/hostpgen \
	     CROSS_COMPILE_TARGET=yes

	make install HOSTPYTHON=./hostpython CROSS_COMPILE_TARGET=yes prefix="$PWD/_install-simulator"

	pushd _install-simulator/lib
	mv libpython2.7.a libpython2.7-i386.a
	popd

	pushd _install-simulator
	mkdir $PATH_SIMU
	cp -R . $PATH_SIMU
	popd

	make distclean
#fi

export MACOSX_DEPLOYMENT_TARGET=

echo "Building for iOS ======================================================="
# set up environment variables for cross compilation
export DEVROOT="/Developer/Platforms/iPhoneOS.platform/Developer"
export SDKROOT="$DEVROOT/SDKs/iPhoneOS${IOS_VERSION}.sdk"

if [ ! -d "$DEVROOT" ]; then
    echo "DEVROOT doesn't exist. DEVROOT=$DEVROOT"
    exit 1
fi

if [ ! -d "$SDKROOT" ]; then
    echo "SDKROOT doesn't exist. SDKROOT=$SDKROOT"
    exit 1
fi

export CPPFLAGS="-I$SDKROOT/usr/lib/gcc/arm-apple-darwin11/4.2.1/include/ -I$SDKROOT/usr/include/"
export CFLAGS="$CPPFLAGS -pipe -no-cpp-precomp -isysroot $SDKROOT"
export LDFLAGS="-isysroot $SDKROOT -Lextralibs/"
export CPP="/usr/bin/cpp $CPPFLAGS"

export CFLAGS = "$CFLAGS -march=armv7 -mcpu=arm1176jzf-s -mcpu=cortex-a8"
export LDFLAGS = "$LDFLAGS -march=armv7 -mcpu=arm1176jzf-s -mcpu=cortex-a8"
#export CFLAGS = "$CFLAGS -march=armv7"
#export LDFLAGS = "$LDFLAGS -march=armv7"

# make a link to a differently named library for who knows what reason
mkdir extralibs||echo "foo"
ln -s "$SDKROOT/usr/lib/libgcc_s.1.dylib" extralibs/libgcc_s.10.4.dylib || echo "sdf"
#ln -s "$SDKROOT/usr/lib/libgcc_s.1.dylib" extralibs/libgcc_s.10.6.dylib || echo "sdf"

# Compile some stuff statically; Modules/Setup taken from pgs4a-kivy
cp ../python_files/ModulesSetup Modules/Setup.local

# Put arm compiler in path, then ccache can use it
OLDPATH=$PATH
export PATH=$PATH:$DEVROOT/usr/bin

# XXX Should prolly use armv7 as well?
./configure CC="arm-apple-darwin10-llvm-gcc-4.2" \
            LD="$DEVROOT/usr/bin/ld" --disable-toolbox-glue --host=armv7-apple-darwin --prefix=/python
#	    --without-doc-strings

make HOSTPYTHON=./hostpython HOSTPGEN=./Parser/hostpgen \
     CROSS_COMPILE_TARGET=yes

make install HOSTPYTHON=./hostpython CROSS_COMPILE_TARGET=yes prefix="$PWD/_install"

# Restore old path
export PATH=$OLDPATH

pushd _install/lib
mv libpython2.7.a libpython2.7-arm.a
#lipo -create -output libpython2.7.a ../../libpython2.7-i386.a libpython2.7-arm.a
popd
pushd _install
mkdir $PATH_DEV
cp -R . $PATH_DEV

mkdir $PATH_ALL
cp -R . $PATH_ALL

lipo $PATH_DEV/lib/libpython2.7-arm.a $PATH_SIMU/lib/libpython2.7-i386.a -create -output $PATH_ALL/lib/libpython2.7-iOS5.a
#find python2.7 | grep -E '*\.(py|pyc|so\.o|so\.a|so\.libs)$' | xargs rm
#find python2.7 | grep -E '*test*' | xargs rm -rdf

cp $PATH_DEV/lib/libpython2.7-arm.a $BUILDROOT/lib/
