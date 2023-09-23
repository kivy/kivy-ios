
#!/bin/bash

set -eo pipefail

toolchain create Touchtracer kivy-ci-clone/examples/demo/touchtracer

# If runner arch is arm64, then the simulator arch is arm64,
# otherwise it's x86_64
if [ $(arch) == "arm64" ]; then
    SIM_ARCH="arm64"
else
    SIM_ARCH="x86_64"
fi

# Build for iOS
xcodebuild -project touchtracer-ios/touchtracer.xcodeproj \
            -scheme touchtracer \
            -destination generic/platform=iOS\
            clean build CODE_SIGNING_ALLOWED=NO | xcpretty

# Build for iOS Simulator
xcodebuild -project touchtracer-ios/touchtracer.xcodeproj \
            -scheme touchtracer \
            -destination 'generic/platform=iOS Simulator' \
            clean build CODE_SIGNING_ALLOWED=NO ARCHS=$SIM_ARCH | xcpretty