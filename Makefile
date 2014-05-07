
all: iphoneos iphonesimulator
	./tools/link-fat-lib.sh

iphoneos:
	mkdir -p build/armv7; \
	cp -r tools  build/armv7/tools; \
	cp -r src  build/armv7/src; \
	export TARGET_SDK=iphoneos; \
	TARGET_SDK=iphoneos build/armv7/tools/build-all.sh; \
	rm -rf tmp; \
	mkdir -p tmp/; \
       	cp -r build/armv7/tmp/Python-2.7.1 tmp/Python-2.7.1; \
	rm -rf build/armv7/tools build/armv7/src build/armv7/tmp; \
	mv build/armv7/build/* build/armv7/; \
	rm -r build/armv7/build; \
	libtool -static -o build/armv7/lib/kivy-ios-all.a build/armv7/lib/lib*;


iphonesimulator:
	mkdir -p build/i386; \
	cp -r tools  build/i386/tools; \
	cp -r src  build/i386/src; \
	export TARGET_SDK=iphonesimulator; \
	TARGET_SDK=iphonesimulator build/i386/tools/build-all.sh; \
	rm -rf build/i386/tools build/i386/src build/i386/tmp; \
	mv build/i386/build/* build/i386/; \
	rm -r build/i386/build; \
	libtool -static -o build/i386/lib/kivy-ios-all.a build/i386/lib/lib*; 
	
clean:
	rm -rf ./build
