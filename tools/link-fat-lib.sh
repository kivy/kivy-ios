#!/bin/bash

echo "== Building fat lib for iphoneos armv7 and simulator i386 ============="

. $(dirname $0)/environment.sh

rm -rf $BUILDROOT/include
rm -rf $BUILDROOT/python
rm -rf $BUILDROOT/pkgconfig
rm -rf $BUILDROOT/lib


cp -r $BUILDROOT/armv7/include $BUILDROOT/include
cp -r $BUILDROOT/armv7/python $BUILDROOT/python
cp -r $BUILDROOT/armv7/pkgconfig $BUILDROOT/pkgconfig
mkdir -p $BUILDROOT/lib
lipo -create -o $BUILDROOT/lib/kivy-ios-fat.a $BUILDROOT/i386/lib/kivy-ios-all.a $BUILDROOT/armv7/lib/kivy-ios-all.a 
