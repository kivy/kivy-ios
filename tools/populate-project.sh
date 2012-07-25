#!/bin/bash

try () {
	"$@" || exit -1
}

. $(dirname $0)/environment.sh

APPNAME=$1
APPID=$(echo $APPNAME | tr '[A-Z]' '[a-z]')
APPDIR=$KIVYIOSROOT/app-$APPID
SRCDIR=$2

if [ "X$APPNAME" == "X" ]; then
	echo $(basename $0) "<appname> <source directory>"
	exit 1
fi

if [ "X$SRCDIR" == "X" ]; then
	echo $(basename $0) "<appname> <source directory>"
	exit 1
fi

echo "-> Copy $SRCDIR to $APPDIR/YourApp"
YOURAPPDIR=$APPDIR/YourApp

echo "-> Remove any previous YourApp version"
if [ -e $YOURAPPDIR ]; then
	rm -r $YOURAPPDIR
fi

echo "-> Copy the new source"
try cp -a $SRCDIR $YOURAPPDIR

echo "-> Compile to pyo"
$TMPROOT/Python-$PYTHON_VERSION/hostpython -OO -m compileall $YOURAPPDIR

echo "-> Remove unused files (pyc, py)"
find $YOURAPPDIR -iname '*.py' -exec rm {} \;
find $YOURAPPDIR -iname '*.pyc' -exec rm {} \;


echo "-> Source code of $APPNAME updated."

