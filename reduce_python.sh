#!/bin/bash

echo "Starting reducing=========="

pushd $BUILDROOT/python/lib/python2.7
find . -iname '*.pyc' | xargs rm
find . -iname '*.py' | xargs rm
find . -iname 'test_*' | xargs rm -rf
rm -rf *test* config lib* wsgiref bsddb curses idlelib hotshot || true
popd
rm -rf pkgconfig || true
