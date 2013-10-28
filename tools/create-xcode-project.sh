#!/bin/bash

try () {
	"$@" || exit -1
}

. $(dirname $0)/environment.sh

APPNAME=$1
SRCDIR=$2
APPID=$(echo $APPNAME | tr '[A-Z]' '[a-z]')
TEMPLATESDIR=$(dirname $0)/templates/
APPDIR=$KIVYIOSROOT/app-$APPID
OLD_LC_CTYPE=$LC_CTYPE
OLD_LANG=$LANG

# fix for -> sed: RE error: illegal byte sequence
LC_CTYPE=C
LANG=C

if [ "X$APPNAME" == "X" ]; then
	echo $(basename $0) "<appname> <source directory>"
	exit 1
fi

if [ "X$SRCDIR" == "X" ]; then
	echo $(basename $0) "<appname> <source directory>"
	exit 1
fi


echo "-> Create $APPDIR directory"
try mkdir $APPDIR

echo "-> Copy templates"
try cp $TEMPLATESDIR/main.m $APPDIR/main.m
#try cp $TEMPLATESDIR/bridge.h $APPDIR/bridge.h
#try cp $TEMPLATESDIR/bridge.m $APPDIR/bridge.m
try cp $TEMPLATESDIR/icon.png $APPDIR/icon.png
try cp $TEMPLATESDIR/template-Info.plist $APPDIR/$APPID-Info.plist
try cp -a $TEMPLATESDIR/template.xcodeproj $APPDIR/$APPID.xcodeproj

echo "-> Customize templates"
try find $APPDIR -type f -not -iname *.png -exec sed -i '' "s/##APPID##/$APPID/g" {} \;
try find $APPDIR -type f -not -iname *.png -exec sed -i '' "s/##APPNAME##/$APPNAME/g" {} \;
try find $APPDIR -type f -not -iname *.png -exec sed -i '' "s/##SDKVER##/$SDKVER/g" {} \;
try find $APPDIR -type f -not -iname *.png -exec sed -i '' "s^##SRCDIR##^$SRCDIR^g" {} \;

LC_CTYPE=$OLD_LC_CTYPE
LANG=$OLD_LANG

echo "-> Done !"
echo
echo "Your project is available at $APPDIR"
echo
echo "You can now type: open $APPDIR/$APPID.xcodeproj"
echo
