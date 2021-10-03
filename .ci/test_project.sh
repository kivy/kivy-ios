
#!/bin/bash

set -eo pipefail

toolchain create Touchtracer kivy-ci-clone/examples/demo/touchtracer

xcodebuild -project touchtracer-ios/touchtracer.xcodeproj \
            -scheme touchtracer \
            -destination generic/platform=iOS\
            clean build CODE_SIGNING_ALLOWED=NO | xcpretty