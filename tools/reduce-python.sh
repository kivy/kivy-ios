#!/bin/bash

. environment.sh

echo "Starting reducing=========="

try cd $BUILDROOT/python/lib/python2.7
find . -iname '*.pyc' | xargs rm
find . -iname '*.py' | xargs rm
find . -iname 'test*' | xargs rm -rf
rm -rf *test* lib* wsgiref bsddb curses idlelib hotshot || true
rm -rf 
try cd ..
rm -rf pkgconfig || true
