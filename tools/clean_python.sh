#!/bin/zsh
set -o errexit
set -x

echo "Starting cleaning=========="

# credit to:
# http://randomsplat.com/id5-cross-compiling-python-for-embedded-linux.html
# http://latenitesoft.blogspot.com/2008/10/iphone-programming-tips-building-unix.html

export IOS_VERSION="5.0"
PATH_SIMU=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}-simulator
PATH_DEV=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}-device
PATH_ALL=${PWD}/python_files/Python-2.7.1-IOS${IOS_VERSION}


# get rid of old build
rm -rf Python-2.7.1
rm -rf $PATH_SIMU
rm -rf $PATH_DEV
rm -rf $PATH_ALL
if [[ -a libpython2.7-iOS5.a ]]; then
   rm -fr libpython2.7-iOS5.a
fi
