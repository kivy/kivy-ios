#!/bin/bash

. $(dirname $0)/environment.sh

if [ -f $BUILDROOT/python/lib/python27.zip ]; then
	echo "Python already reduced and compressed."
	exit 0
fi

echo "Starting reducing python 2.7"

try cd $BUILDROOT/python/lib/python2.7
find . -iname '*.pyc' | xargs rm
find . -iname '*.py' | xargs rm
find . -iname 'test*' | xargs rm -rf
rm -rf *test* lib* wsgiref bsddb curses idlelib hotshot || true
try cd ..
rm -rf pkgconfig || true

echo "Compressing to python27.zip"
try pushd $BUILDROOT/python/lib/python2.7
rm config/libpython2.7.a config/python.o config/config.c.in config/makesetup
mv config ..
mv site-packages ..
zip -r ../python27.zip *
rm -rf *
mv ../config .
mv ../site-packages .
popd
