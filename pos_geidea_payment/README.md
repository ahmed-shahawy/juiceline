# Geidea POS Payment Integration - iPad Optimized

A comprehensive Geidea payment integration module specifically optimized for iPad and iOS devices within Odoo Point of Sale.

## Features

### 🍎 iPad/iOS Optimizations
- **Native iOS UI Components**: Touch-friendly interface designed for iPad
- **Bluetooth Management**: Robust Bluetooth Low Energy connection handling
- **Background State Handling**: Smart management of iOS app states (foreground/background)
- **Battery Optimization**: Intelligent power management for extended operation
- **iPad Gestures**: Support for iPad-specific touch gestures and interactions
- **Multi-screen Support**: Responsive design for different iPad screen sizes
- **Split View Compatible**: Optimized layout for iPad Split View and Slide Over

### 🔒 Security & Storage
- **iOS Keychain Integration**: Secure storage using Web Crypto API and IndexedDB
- **Encrypted Data Storage**: All sensitive payment data is encrypted at rest
- **Device-specific Encryption**: Keys are tied to specific iOS devices
- **Secure Communication**: Encrypted Bluetooth communication with payment terminals
- **Permission Management**: Proper handling of iOS security permissions

### 💳 Payment Processing
- **Real-time Transactions**: Fast and reliable payment processing
- **Multiple Payment Methods**: Support for credit/debit cards, digital wallets
- **Partial Payments**: Support for split payments and partial refunds
- **Transaction State Management**: Robust handling of payment states and interruptions
- **Offline Capability**: Queue transactions when connection is temporarily lost
- **Receipt Generation**: Automatic receipt creation and management

### 🔗 Connection Management
- **Auto-discovery**: Automatic Bluetooth device discovery and pairing
- **Smart Reconnection**: Intelligent reconnection with exponential backoff
- **Connection Health Monitoring**: Real-time monitoring of connection quality
- **Multiple Device Support**: Ability to connect to different Geidea terminals
- **Connection History**: Detailed logging of connection events and issues

### 📊 Monitoring & Analytics
- **Real-time Status**: Live connection and payment status indicators
- **Performance Metrics**: Transaction processing time and success rates
- **Battery Monitoring**: iOS battery level tracking and optimization
- **Thermal Management**: CPU and thermal state monitoring for iOS devices
- **Connection Diagnostics**: Detailed Bluetooth connection diagnostics

## Installation

1. Copy the module to your Odoo addons directory:
   ```bash
   cp -r pos_geidea_payment /path/to/odoo/addons/
   ```

2. Update the addons list:
   ```bash
   ./odoo-bin -u all -d your_database
   ```

3. Install the module from the Apps menu in Odoo

## Configuration

### POS Configuration
1. Go to **Point of Sale > Configuration > Point of Sale**
2. Select your POS configuration
3. Enable "Geidea Payment Integration"
4. Configure the following settings:
   - **Merchant ID**: Your Geidea merchant identifier
   - **Merchant Key**: Your Geidea API key
   - **Device Name**: Name of your Geidea payment terminal
   - **Test Mode**: Enable for testing (recommended initially)
   - **iPad Optimized**: Enable iPad-specific optimizations
   - **Auto Reconnect**: Enable automatic reconnection
   - **Battery Optimization**: Enable power management features

### Security Setup
1. Ensure your Odoo instance is running over HTTPS (required for Web Crypto API)
2. Configure proper SSL certificates for production use
3. Set up appropriate user permissions for POS users

## Usage

### Basic Payment Flow
1. **Connect Device**: Use the connection widget to pair with your Geidea terminal
2. **Process Payment**: Enter amount and tap "Process Payment"
3. **Customer Interaction**: Customer completes payment on the terminal
4. **Confirmation**: Transaction is automatically recorded in Odoo

### iPad-Specific Features
- **Touch Gestures**: Swipe to refresh connection, pinch to zoom on transaction details
- **Orientation Support**: Automatic layout adjustment for portrait/landscape
- **Split View**: Compact layout when used in iPad Split View
- **Background Handling**: Maintains connection when app goes to background

### Connection Management
- **Auto-Discovery**: Scan for nearby Geidea devices
- **Manual Connection**: Connect to specific devices by name or MAC address
- **Connection Status**: Real-time status indicators with detailed information
- **Reconnection**: Automatic reconnection when connection is lost

### Security Features
- **Secure Storage**: All payment credentials stored in encrypted format
- **Device Binding**: Encryption keys tied to specific iOS devices
- **Permission Handling**: Proper request and management of iOS permissions
- **Data Protection**: Sensitive data is never stored in plain text

## Architecture

### Frontend Components
- **GeideaPaymentModel**: Core payment processing logic
- **GeideaBluetoothManager**: Bluetooth connection management
- **IOSBluetoothAdapter**: iOS-specific Bluetooth optimizations
- **IOSKeychainManager**: Secure storage management
- **IOSPowerManager**: Battery and power optimization
- **GeideaPaymentScreen**: Main payment interface
- **GeideaConnectionWidget**: Connection status widget
- **GeideaPaymentButton**: Payment action button

### Backend Components
- **pos.config**: POS configuration extensions
- **geidea.payment**: Payment transaction model
- **pos.order**: Order integration
- **Controllers**: API endpoints for payment processing

### Security Layer
- **Web Crypto API**: Modern encryption standards
- **IndexedDB**: Secure local storage
- **Device Fingerprinting**: Unique device identification
- **Key Derivation**: PBKDF2 with device-specific salts

## API Reference

### JavaScript Models

#### GeideaPaymentModel
```javascript
// Initialize payment
const payment = new GeideaPaymentModel(pos);

// Process payment
const result = await payment.processPayment(amount, currency, orderRef);

// Check connection status
const isConnected = payment.isConnected();
```

#### IOSBluetoothAdapter
```javascript
// Connect to device
const adapter = new IOSBluetoothAdapter(settings);
await adapter.connect(deviceId);

// Monitor connection
adapter.addEventListener('stateChange', (event) => {
    console.log('Connection state:', event.detail.newState);
});
```

#### IOSKeychainManager
```javascript
// Store secure data
const keychain = new IOSKeychainManager();
await keychain.storeSecureData('credentials', {
    merchantId: 'your_merchant_id',
    merchantKey: 'your_merchant_key'
});

// Retrieve secure data
const credentials = await keychain.getSecureData('credentials');
```

### Backend API

#### Payment Processing
```python
# Create payment transaction
payment = env['geidea.payment'].create({
    'amount': 100.0,
    'currency_id': currency.id,
    'reference': 'Order #001',
    'pos_session_id': session.id
})

# Process payment
result = payment.action_authorize()
```

#### Configuration
```python
# Configure POS for Geidea
pos_config.write({
    'geidea_payment_enabled': True,
    'geidea_merchant_id': 'your_merchant_id',
    'geidea_merchant_key': 'your_merchant_key',
    'geidea_ipad_optimized': True
})
```

## Troubleshooting

### Common Issues

#### Bluetooth Connection Problems
- Ensure Bluetooth is enabled on the iPad
- Check that the Geidea terminal is in pairing mode
- Verify the device is within range (typically 10 meters)
- Try restarting the Bluetooth service on the iPad

#### Payment Processing Errors
- Verify merchant credentials are correct
- Check network connectivity
- Ensure the terminal has sufficient battery
- Review transaction logs in the Geidea dashboard

#### iOS-Specific Issues
- Ensure the app has Bluetooth permissions
- Check that iOS version is supported (iOS 14+)
- Verify the web app is running in a secure context (HTTPS)
- Clear browser cache and reload the application

### Logging and Debugging
Enable debug logging in Odoo configuration:
```ini
[logger_geidea]
level = DEBUG
handlers = console
qualname = pos_geidea_payment
```

Check browser console for JavaScript errors and Bluetooth API messages.

## Support

### Requirements
- **Odoo**: Version 18.0 or later
- **iOS**: Version 14.0 or later
- **Browser**: Safari 14+ or Chrome 90+ on iOS
- **Geidea Terminal**: Compatible Bluetooth LE models
- **SSL**: HTTPS required for security features

### Browser Compatibility
- ✅ Safari on iOS 14+
- ✅ Chrome on iOS 90+
- ✅ Edge on iOS 44+
- ❌ Firefox (limited Bluetooth support)

### Hardware Compatibility
- ✅ iPad Pro (all models)
- ✅ iPad Air (3rd generation and later)
- ✅ iPad (8th generation and later)
- ✅ iPad mini (5th generation and later)
- ⚠️ iPhone (limited screen space)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This module is licensed under LGPL-3. See LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- iPad-optimized UI
- Bluetooth LE integration
- iOS Keychain security
- Power management
- Real-time payment processing
- Connection management
- Comprehensive error handling

---

**Developed for Odoo 18.0 with iPad/iOS optimization focus**