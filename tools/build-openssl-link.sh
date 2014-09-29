#!/bin/bash

. $(dirname $0)/environment.sh

echo "Modifying Python Setup.dist..."
cp $TMPROOT/Python-2.7.1/Modules/Setup.dist $KIVYIOSROOT/src/python_files

SETUP_DIST=$KIVYIOSROOT/src/python_files/Setup.dist
echo "" >> $SETUP_DIST
echo "# Adding SSL Links" >> $SETUP_DIST
echo "# Socket module helper for sockets" >> $SETUP_DIST
echo "_socket socketmodule.c" >> $SETUP_DIST
echo "SSL=$TMPROOT/openssl/ios-openssl/openssl" >> $SETUP_DIST
echo "_ssl _ssl.c \\" >> $SETUP_DIST
echo "       -DUSE_SSL -I\$(SSL)/include -I\$(SSL)/include/openssl \\" >> $SETUP_DIST
echo "       -L\$(SSL)/lib -lssl -lcrypto" >> $SETUP_DIST

echo "Cleaning and rebuilding Python to inlcude SSL links..."
sh $KIVYIOSROOT/tools/clean_python.sh
sh $KIVYIOSROOT/tools/build-python.sh
