# Juiceline - Geidea Payment Integration Platform

A comprehensive iOS SDK and backend integration for Geidea payment devices, built for modern POS systems.

## Project Overview

This repository contains:
- **JuicelineGeideaSDK**: Swift iOS SDK for Geidea device integration
- **Legacy POS Module**: Existing Odoo-based loyalty system (pos_bonat_loyalty)

## 🚀 Sprint 1 - Core Infrastructure (COMPLETED)

### ✅ Delivered Features

#### 1. iOS SDK Development
- **Core Integration Module**: Swift protocols and classes for device communication
- **Bluetooth Connectivity**: Cross-platform Bluetooth device discovery and management
- **Payment Processing**: Secure payment transaction handling with concurrency support
- **Receipt Management**: Automated receipt generation and handling
- **Testing Framework**: Comprehensive unit tests and mock implementations

#### 2. Development Environment
- **Development Containers**: Docker-based development environment
- **CI/CD Pipeline**: Automated testing, security scanning, and documentation generation
- **Code Quality**: SwiftLint integration for consistent code style
- **Cross-Platform Support**: iOS, macOS, and Linux compatibility

#### 3. Architecture & Testing
- **Protocol-Oriented Design**: Flexible, testable architecture
- **Concurrency Safety**: Thread-safe payment processing
- **Error Handling**: Comprehensive error types and handling
- **Performance Benchmarks**: Built-in performance testing tools

## 📱 SDK Features

### Core Components

#### GeideaDeviceProtocol
```swift
protocol GeideaDeviceProtocol {
    func connect() async throws
    func disconnect() async
    func processPayment(_ amount: Decimal) async throws -> PaymentResult
}
```

#### GeideaConnectionManager
- Device discovery and connection management
- Bluetooth state monitoring
- Multiple device support
- Thread-safe operations

#### GeideaPaymentProcessor
- Payment transaction processing
- Receipt generation and handling
- Concurrent payment support
- Error handling and recovery

### Quick Start

```swift
import JuicelineGeideaSDK

// Initialize SDK
let sdk = JuicelineGeideaSDK.shared
try await sdk.initialize()

// Discover devices
let devices = try await sdk.getAvailableDevices()

// Connect and process payment
let deviceInstance = sdk.createDeviceInstance(for: devices.first!)
try await deviceInstance.connect()
let result = try await deviceInstance.processPayment(25.99)
```

## 🏗️ Development Setup

### Prerequisites
- Xcode 14.0+
- Swift 5.9+
- iOS 14.0+ / macOS 11.0+

### Installation

#### Swift Package Manager
```swift
dependencies: [
    .package(url: "https://github.com/ahmed-shahawy/juiceline.git", from: "1.0.0")
]
```

#### Development Container
```bash
# Open in VS Code with Dev Containers
code .
# Select "Reopen in Container"
```

### Building and Testing

```bash
cd JuicelineGeideaSDK

# Build the project
swift build

# Run tests
swift test

# Run with coverage
swift test --enable-code-coverage
```

## 📊 Project Statistics

- **18 Unit Tests**: All passing ✅
- **6 Core Swift Modules**: Fully implemented
- **Cross-Platform**: iOS, macOS, Linux support
- **Thread-Safe**: Concurrent payment processing
- **Zero Dependencies**: Minimal external dependencies

## 🛠️ CI/CD Pipeline

### Automated Workflows
- ✅ **Swift Package Building**: Automated builds on push/PR
- ✅ **Testing**: Comprehensive test suite execution
- ✅ **Code Quality**: SwiftLint static analysis
- ✅ **Security Scanning**: Trivy vulnerability scanning
- ✅ **Documentation**: Auto-generated API documentation

### Code Quality Metrics
- **SwiftLint**: Enforced coding standards
- **Test Coverage**: Unit test coverage reporting
- **Performance**: Built-in benchmarking tools

## 📁 Project Structure

```
juiceline/
├── JuicelineGeideaSDK/          # Swift iOS SDK
│   ├── Sources/
│   │   ├── JuicelineGeideaSDK/     # Core SDK modules
│   │   └── JuicelineGeideaSDKTesting/  # Testing utilities
│   ├── Tests/                   # Unit tests
│   ├── Examples/                # Usage examples
│   └── Benchmarks/             # Performance tests
├── .devcontainer/              # Development environment
├── .github/workflows/          # CI/CD configuration
└── pos_bonat_loyalty_18 v2/    # Legacy Odoo module
```

## 🎯 Sprint 2 Roadmap

### Planned Features
- [ ] Advanced payment features (refunds, partial payments)
- [ ] Enhanced error handling and recovery
- [ ] Performance optimizations
- [ ] Extended device support
- [ ] Analytics integration
- [ ] Offline payment capabilities

### Technical Debt
- [ ] Add integration tests with real devices
- [ ] Implement comprehensive logging
- [ ] Add network layer for cloud connectivity
- [ ] Enhance documentation with more examples

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

### Development Guidelines
- Follow SwiftLint rules
- Add tests for new functionality
- Update documentation
- Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [SDK Documentation](https://ahmed-shahawy.github.io/juiceline/)
- [API Reference](./JuicelineGeideaSDK/README.md)
- [Usage Examples](./JuicelineGeideaSDK/Examples/)
- [Contributing Guidelines](./CONTRIBUTING.md)