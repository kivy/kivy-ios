#!/bin/bash

try () {
	"$@" || exit -1
}

. $(dirname $0)/environment.sh

export PYTHONDONTWRITEBYTECODE=

APPNAME=$1
APPID=$(echo $APPNAME | tr '[A-Z]' '[a-z]')
APPDIR=$KIVYIOSROOT/app-$APPID
SRCDIR=$2

set -x
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

echo "-> Synchronize source code"
try rsync -av --delete $SRCDIR/ $YOURAPPDIR

echo "-> Compile to pyo"
#$HOSTPYTHON -OO -m compileall $YOURAPPDIR
python -OO -m compileall $YOURAPPDIR

#echo "-> Remove unused files (pyc, py)"
#find $YOURAPPDIR -iname '*.py' -exec rm {} \;
#find $YOURAPPDIR -iname '*.pyc' -exec rm {} \;

echo "-> Source code of $APPNAME updated."
