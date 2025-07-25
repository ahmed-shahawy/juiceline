# Geidea Payment Terminal Integration

Cross-platform Geidea payment terminal integration for Odoo POS.

## Features

### Cross-Platform Support
- **Windows**: USB, Serial, Network, Bluetooth connections
- **iOS/iPad**: Bluetooth and Network connections 
- **Android**: USB OTG, Bluetooth, and Network connections
- **Auto-detection**: Automatic platform detection and capability checking

### Connection Management
- Multiple connection types: USB, Bluetooth, Network, Serial
- Automatic terminal discovery and connection
- Real-time connection status monitoring
- Auto-reconnection with configurable retry logic
- Platform-specific connection optimizations

### Payment Processing
- Seamless integration with Odoo POS payment flow
- Real-time transaction processing
- Comprehensive error handling and user feedback
- Receipt integration (POS and/or terminal receipts)

### User Interface
- Responsive design for all screen sizes
- Touch-friendly controls for mobile devices
- Real-time terminal status display
- Connection management interface
- Platform-specific UI optimizations

## Installation

1. Copy the `pos_geidea_payment` module to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the module from the Apps menu
4. Configure Geidea terminals in POS settings

## Configuration

### Terminal Setup
1. Go to Point of Sale → Geidea Terminals
2. Create a new terminal with:
   - Terminal Name
   - Terminal ID (from Geidea)
   - Merchant ID (from Geidea)
   - Terminal Key (from Geidea)
   - Connection type (USB/Bluetooth/Network/Serial)
   - Platform (auto-detected)
   - Connection details (IP, port, etc.)

### POS Configuration
1. Go to Point of Sale → Configuration → Point of Sale
2. Edit your POS configuration
3. In the "Geidea Terminals" tab:
   - Select terminals to use
   - Configure auto-connect behavior
   - Set payment timeout
   - Choose receipt options

### Payment Method
1. Go to Point of Sale → Configuration → Payment Methods
2. Create or edit a payment method
3. Set "Use a Payment Terminal" to "Geidea Terminal"
4. Select the specific terminal (optional)

## Platform-Specific Notes

### Windows
- Supports all connection types
- USB drivers may be required
- Serial port connections use COM ports
- Administrator privileges may be needed for USB access

### iOS/iPad
- Supports Bluetooth and Network connections
- USB connections not supported
- Bluetooth pairing must be done in iOS Settings first
- Network connections work over WiFi

### Android
- Supports USB OTG, Bluetooth, and Network connections
- USB debugging may need to be enabled
- Bluetooth pairing in Android Settings required
- Network connections work over WiFi or mobile data

## Testing

The module includes comprehensive test suites:

### Platform Tests
```javascript
import { runGeideaTests } from './static/src/tests/platform_tests.js';
runGeideaTests();
```

### Connection Stability Tests
```javascript
import { ConnectionStabilityTest } from './static/src/tests/platform_tests.js';
const test = new ConnectionStabilityTest(connectionManager);
await test.testConnectionStability(terminalConfig);
```

### Performance Benchmarks
```javascript
import { PerformanceBenchmark } from './static/src/tests/platform_tests.js';
const benchmark = new PerformanceBenchmark(connectionManager);
await benchmark.benchmarkConnectionTime(terminalConfig);
```

## Troubleshooting

### Connection Issues
1. Check terminal status in the connection manager
2. Verify network connectivity (for network connections)
3. Ensure Bluetooth pairing (for Bluetooth connections)
4. Check USB drivers and permissions (for USB connections)

### Platform-Specific Issues
- **Windows**: Check Device Manager for USB devices
- **iOS**: Verify Bluetooth pairing in Settings
- **Android**: Enable USB debugging and check permissions

### Error Messages
The module provides detailed error messages for:
- Connection failures
- Platform incompatibilities
- Payment processing errors
- Terminal communication issues

## API Reference

### Connection Manager
```javascript
// Connect to terminal
await connectionManager.connect(terminalConfig);

// Send payment request
await connectionManager.sendPaymentRequest(terminalId, paymentData);

// Get connection status
const status = connectionManager.getConnectionStatus(terminalId);

// Disconnect
await connectionManager.disconnect(terminalId);
```

### Platform Detector
```javascript
const detector = new PlatformDetector();
const platform = detector.platform;
const capabilities = detector.capabilities;
const recommendations = detector.getRecommendedConnections();
```

## Support

For technical support and feature requests, please contact the development team.

## License

This module is licensed under the Odoo Proprietary License v1.0 (OPL-1).