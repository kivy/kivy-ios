
all: iphoneos iphonesimulator
	echo "Building fat lib"; 

iphoneos:
	mkdir -p build/armv7; \
	cp -r tools  build/armv7/tools; \
	cp -r src  build/armv7/src; \
	export TARGET_SDK=iphoneos; \
	TARGET_SDK=iphoneos build/armv7/tools/build-all.sh;

iphonesimulator:
	mkdir -p build/i386; \
	cp -r tools  build/i386/tools; \
	cp -r src  build/i386/src; \
	export TARGET_SDK=iphonesimulator; \
	TARGET_SDK=iphonesimulator build/i386/tools/build-all.sh;
	
clean:
	rm -rf ./build
