// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "JuicelineGeideaSDK",
    platforms: [
        .iOS(.v14),
        .macOS(.v11)
    ],
    products: [
        .library(
            name: "JuicelineGeideaSDK",
            targets: ["JuicelineGeideaSDK"]),
        .library(
            name: "JuicelineGeideaSDKTesting",
            targets: ["JuicelineGeideaSDKTesting"]),
    ],
    dependencies: [
        // Add external dependencies here
        .package(url: "https://github.com/apple/swift-algorithms", from: "1.0.0")
    ],
    targets: [
        .target(
            name: "JuicelineGeideaSDK",
            dependencies: [
                .product(name: "Algorithms", package: "swift-algorithms")
            ],
            path: "Sources/JuicelineGeideaSDK"
        ),
        .target(
            name: "JuicelineGeideaSDKTesting",
            dependencies: ["JuicelineGeideaSDK"],
            path: "Sources/JuicelineGeideaSDKTesting"
        ),
        .testTarget(
            name: "JuicelineGeideaSDKTests",
            dependencies: [
                "JuicelineGeideaSDK",
                "JuicelineGeideaSDKTesting"
            ],
            path: "Tests/JuicelineGeideaSDKTests"
        ),
    ]
)