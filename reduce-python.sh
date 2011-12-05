#!/bin/zsh
set -o errexit
set -x

echo "Starting reducing=========="

# credit to:
# http://randomsplat.com/id5-cross-compiling-python-for-embedded-linux.html
# http://latenitesoft.blogspot.com/2008/10/iphone-programming-tips-building-unix.html

export IOS_VERSION="5.0"
PATH_SIMU=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}-simulator
PATH_DEV=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}-device
PATH_ALL=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}

pushd $PATH_DEV/lib/python2.7
find . -iname '*.pyc' | xargs rm
find . -iname '*.py' | xargs rm
rm -rd *test*
rm -rd lib-* wsgiref bsddb curses idlelib hotshot
