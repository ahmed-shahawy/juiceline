# Juiceline Geidea SDK

## Overview

The Juiceline Geidea SDK provides a comprehensive solution for integrating Geidea payment devices into iOS applications. This SDK enables Bluetooth connectivity, payment processing, and receipt handling for Geidea POS terminals.

## Features

- 🔗 **Bluetooth Device Management**: Automatic device discovery and connection management
- 💳 **Payment Processing**: Secure payment transaction handling
- 🧾 **Receipt Management**: Automated receipt generation and handling
- 🧪 **Testing Support**: Comprehensive testing utilities and mock implementations
- 📱 **iOS Native**: Built specifically for iOS with Swift

## Requirements

- iOS 14.0+
- macOS 11.0+
- Swift 5.9+
- Xcode 14.0+

## Installation

### Swift Package Manager

Add the following to your `Package.swift` file:

```swift
dependencies: [
    .package(url: "https://github.com/ahmed-shahawy/juiceline.git", from: "1.0.0")
]
```

Or add it through Xcode:
1. File → Add Package Dependencies
2. Enter the repository URL
3. Select the version or branch

## Quick Start

### 1. Initialize the SDK

```swift
import JuicelineGeideaSDK

// Initialize the SDK
let sdk = JuicelineGeideaSDK.shared
try await sdk.initialize()
```

### 2. Discover Devices

```swift
// Scan for available Geidea devices
let devices = try await sdk.getAvailableDevices()
print("Found \(devices.count) devices")
```

### 3. Connect to a Device

```swift
// Create device instance
let deviceInstance = sdk.createDeviceInstance(for: devices.first!)

// Connect to device
try await deviceInstance.connect()
```

### 4. Process Payments

```swift
// Process a payment
let amount: Decimal = 25.50
let result = try await deviceInstance.processPayment(amount)

print("Transaction ID: \(result.transactionId)")
print("Status: \(result.status)")
```

## Architecture

### Core Components

#### GeideaDeviceProtocol
The main protocol defining device communication capabilities:
- `connect()` - Establish device connection
- `disconnect()` - Terminate device connection  
- `processPayment(_:)` - Process payment transactions

#### GeideaConnectionManager
Singleton manager for device discovery and connection:
- Device scanning and discovery
- Connection state management
- Multiple device support

#### GeideaPaymentProcessor
Handles payment processing and receipt management:
- Transaction processing
- Receipt generation
- Error handling

## Testing

The SDK includes comprehensive testing utilities:

```swift
import JuicelineGeideaSDKTesting

// Create mock devices for testing
let mockDevice = GeideaSDKTestingUtils.createMockDevice()
let mockPayment = GeideaSDKTestingUtils.createMockPaymentResult()
```

### Running Tests

```bash
cd JuicelineGeideaSDK
swift test
```

### Test Coverage

```bash
swift test --enable-code-coverage
```

## Error Handling

The SDK provides comprehensive error handling through `GeideaDeviceError`:

```swift
do {
    try await deviceInstance.connect()
} catch GeideaDeviceError.bluetoothUnavailable {
    // Handle Bluetooth unavailable
} catch GeideaDeviceError.deviceNotFound {
    // Handle device not found
} catch GeideaDeviceError.connectionFailed {
    // Handle connection failure
}
```

## Development Environment

### Prerequisites

- Xcode 14.0+
- Swift 5.9+
- macOS 12.0+

### Development Container

Use the provided dev container for consistent development environment:

```bash
# Open in VS Code with Dev Containers extension
code .
# Select "Reopen in Container"
```

### Code Quality

The project uses SwiftLint for code quality:

```bash
swiftlint lint --strict
```

## CI/CD Pipeline

The project includes automated CI/CD with:
- ✅ Automated testing
- 🔍 Code quality checks
- 🛡️ Security scanning
- 📚 Documentation generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Create an issue on GitHub
- Review the documentation
- Check the examples directory

## Roadmap

### Sprint 1 (Current) ✅
- Core infrastructure setup
- Basic device communication
- Payment processing foundation
- Testing framework

### Sprint 2 (Planned)
- Advanced payment features
- Enhanced error handling
- Performance optimizations
- Extended device support

### Sprint 3 (Future)
- Analytics integration
- Offline payment support
- Advanced security features
- Multi-language support