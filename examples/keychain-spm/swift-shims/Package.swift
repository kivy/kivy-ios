// swift-tools-version:5.9
import PackageDescription

// Local @objc shim that wraps the pure-Swift KeychainAccess API in
// Objective-C-representable signatures so pyobjus can call it.  kivy-ios wires
// this in via the `path` form of [tool.kivy.ios.native.swift_packages].
//
// The product is declared `.dynamic` so it builds as a framework kivy-ios can
// embed (a static product would have nothing to copy into .app/Frameworks).
let package = Package(
    name: "KeychainBridge",
    platforms: [.iOS(.v16)],
    products: [
        .library(name: "KeychainBridge", type: .dynamic, targets: ["KeychainBridge"]),
    ],
    dependencies: [
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess", from: "4.2.2"),
    ],
    targets: [
        .target(
            name: "KeychainBridge",
            dependencies: [
                .product(name: "KeychainAccess", package: "KeychainAccess"),
            ]
        ),
    ]
)
