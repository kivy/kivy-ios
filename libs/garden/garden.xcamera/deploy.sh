# deploy to kivy launcher on android
ROOT=/tmp/xcamera-example
XCAMERA=$ROOT/libs/garden/garden.xcamera

echo rm -rf $ROOT
mkdir -p $XCAMERA

cp example/main.py example/android.txt $ROOT
cp *.py $XCAMERA
cp -r data $XCAMERA

adb push $ROOT /sdcard/kivy/xcamera
adb logcat -s python
