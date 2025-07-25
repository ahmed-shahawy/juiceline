# Geidea Payment Integration Documentation

## Overview

The Geidea Payment Integration module provides comprehensive payment terminal integration for Odoo Point of Sale (POS) systems. This module extends the existing Bonat loyalty system with advanced payment processing capabilities, including support for multiple payment methods, partial payments, refunds, and real-time transaction monitoring.

## Key Features

### 1. Terminal Integration
- **Multi-terminal Support**: Manage multiple Geidea payment terminals
- **Real-time Status Monitoring**: Live terminal health and connectivity status
- **Automatic Connection Recovery**: Robust retry mechanisms with exponential backoff
- **Performance Metrics**: Track response times and success rates

### 2. Payment Processing
- **Multiple Payment Methods**: Card, contactless, mobile, and QR code payments
- **Partial Payments**: Support for split transactions and installment payments
- **Refund Processing**: Full and partial refund capabilities with audit trails
- **Transaction Validation**: Multi-layer security and integrity verification

### 3. Security & Compliance
- **Data Encryption**: AES encryption for sensitive payment data
- **Transaction Integrity**: SHA-256 checksums for data verification
- **PCI DSS Compliance**: Secure handling of cardholder data
- **Key Management**: Automatic encryption key generation and rotation

### 4. Performance Optimization
- **Connection Pooling**: Efficient resource management for multiple terminals
- **Asynchronous Processing**: Non-blocking payment operations
- **Intelligent Caching**: Optimized data retrieval and storage
- **Real-time Monitoring**: Performance tracking and alerting

## Installation and Configuration

### Prerequisites
- Odoo 18.0 or later
- Python packages: `requests`, `cryptography`
- Valid Geidea merchant account and API credentials

### Installation Steps

1. **Install the Module**
   ```bash
   # Copy the module to your Odoo addons directory
   cp -r pos_bonat_loyalty /path/to/odoo/addons/
   
   # Update module list and install
   ./odoo-bin -d your_database -i pos_bonat_loyalty --stop-after-init
   ```

2. **Configure Company Settings**
   Navigate to: `Settings > General Settings > Geidea Payment Integration`
   
   Required fields:
   - **API Key**: Your Geidea API key
   - **API Password**: Your Geidea API password
   - **Merchant ID**: Your Geidea merchant identifier
   - **Terminal ID**: Your primary terminal identifier
   - **Environment**: Test or Production environment

3. **Configure Payment Methods**
   Navigate to: `Point of Sale > Configuration > Payment Methods`
   
   Create new payment methods:
   - Set "Is Geidea Payment Method" to True
   - Select the appropriate payment type (card, contactless, etc.)
   - Configure minimum/maximum amounts if needed

4. **Set Up Terminals**
   Navigate to: `Point of Sale > Geidea Payment > Payment Terminals`
   
   Add your terminals:
   - Enter terminal ID and name
   - Configure IP address and port (if applicable)
   - Set connection timeout and other parameters

## Usage Guide

### Basic Payment Processing

1. **Standard Payment**
   - Select items in POS
   - Go to payment screen
   - Select Geidea payment method
   - Enter amount and process payment
   - Follow terminal prompts for card insertion/tap

2. **Partial Payments**
   ```javascript
   // Example: Process partial payment
   await this.processGeideaPartialPayment(50.00, 'card');
   ```

3. **Refund Processing**
   - Find completed transaction
   - Click refund button
   - Enter refund amount and reason
   - Confirm refund processing

### Advanced Features

#### Connection Monitoring
```javascript
// Check terminal health
const health = await this.getTerminalHealth();
console.log('Terminal Status:', health.status);
```

#### Transaction Status Tracking
```javascript
// Check transaction status
const status = await this._checkTransactionStatus(transactionId);
if (status.success) {
    console.log('Transaction State:', status.geidea_data.status);
}
```

#### Performance Metrics
```python
# Get performance metrics (Python/Odoo)
metrics = self.env['geidea.payment.service'].get_performance_metrics()
print(f"Success Rate: {metrics['metrics']['success_rate']}%")
```

## API Reference

### Models

#### GeideaPaymentTerminal
Manages payment terminal configurations and status.

**Fields:**
- `terminal_id`: Unique terminal identifier
- `name`: Human-readable terminal name
- `status`: Current connection status
- `ip_address`: Terminal IP address
- `port`: Communication port
- `last_connection`: Last successful connection timestamp

**Methods:**
- `check_terminal_health(terminal_id)`: Check terminal health status

#### GeideaPaymentTransaction
Tracks individual payment transactions throughout their lifecycle.

**Fields:**
- `name`: Unique transaction reference
- `transaction_id`: Geidea transaction identifier
- `amount`: Transaction amount
- `currency_id`: Transaction currency
- `payment_method`: Payment method type
- `state`: Transaction status
- `checksum`: Data integrity checksum

**Methods:**
- `generate_checksum()`: Generate transaction checksum
- `_encrypt_sensitive_data(data)`: Encrypt sensitive data
- `_decrypt_sensitive_data()`: Decrypt sensitive data

#### GeideaPaymentService
Core service for payment processing operations.

**Methods:**
- `initiate_payment(payment_data)`: Initiate a new payment
- `capture_payment(transaction_id, amount)`: Capture authorized payment
- `refund_payment(transaction_id, amount, reason)`: Process refund
- `check_transaction_status(transaction_id)`: Check transaction status
- `test_connection(terminal_id)`: Test terminal connection

### Controllers

#### GeideaPaymentController
RESTful API endpoints for payment operations.

**Endpoints:**
- `POST /geidea/initiate_payment`: Initiate payment
- `POST /geidea/capture_payment`: Capture payment
- `POST /geidea/refund_payment`: Process refund
- `GET /geidea/check_status/<transaction_id>`: Check status
- `POST /geidea/partial_payment`: Process partial payment
- `GET /geidea/terminal_health/<terminal_id>`: Check terminal health

#### GeideaWebhookController
Handles webhook notifications from Geidea.

**Endpoints:**
- `POST /geidea/webhook/payment_status`: Payment status webhooks

### JavaScript Components

#### GeideaPaymentInterface
Main payment interface for POS integration.

**Methods:**
- `send_payment_request(cid)`: Send payment request
- `send_payment_cancel(order, cid)`: Cancel/refund payment
- `processPartialPayment(orderId, amount, method)`: Process partial payment

#### GeideaTerminalStatus
Real-time terminal status display component.

**Features:**
- Live connection status monitoring
- Performance metrics display
- Error notification and recovery

## Configuration Options

### Company Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `enable_geidea_integration` | Enable/disable Geidea integration | False |
| `geidea_api_key` | Geidea API key | - |
| `geidea_api_password` | Geidea API password | - |
| `geidea_merchant_id` | Merchant identifier | - |
| `geidea_terminal_id` | Primary terminal ID | - |
| `geidea_environment` | Environment (test/production) | test |
| `geidea_connection_timeout` | Connection timeout in seconds | 30 |
| `geidea_enable_partial_payments` | Enable partial payments | True |
| `geidea_enable_refunds` | Enable refunds | True |
| `geidea_max_retry_attempts` | Maximum retry attempts | 3 |
| `geidea_connection_pool_size` | Connection pool size | 5 |

### Payment Method Settings

| Setting | Description |
|---------|-------------|
| `is_geidea_payment` | Mark as Geidea payment method |
| `geidea_payment_type` | Payment type (card/contactless/mobile/qr) |
| `terminal_id` | Associated terminal |
| `enable_partial_payment` | Allow partial payments |
| `minimum_amount` | Minimum transaction amount |
| `maximum_amount` | Maximum transaction amount |

## Security Considerations

### Data Protection
- All sensitive payment data is encrypted using AES-256 encryption
- Encryption keys are automatically generated and stored securely
- Card numbers are masked in all displays and logs
- Transaction checksums ensure data integrity

### API Security
- HTTPS-only communication with Geidea servers
- API key authentication for all requests
- Request signing and validation
- Rate limiting and retry mechanisms

### Compliance
- PCI DSS compliant data handling
- Secure key management practices
- Audit trails for all transactions
- Data retention policies

## Troubleshooting

### Common Issues

#### Connection Problems
```
Error: Terminal not connected
```
**Solution:**
1. Check terminal network connectivity
2. Verify API credentials in settings
3. Test connection using "Test Connection" button
4. Check terminal health status

#### Payment Failures
```
Error: Payment request failed
```
**Solution:**
1. Verify transaction amount and currency
2. Check terminal status and connectivity
3. Review error logs for specific error codes
4. Ensure payment method is properly configured

#### Performance Issues
```
Warning: Slow response times
```
**Solution:**
1. Check network latency to Geidea servers
2. Optimize connection pool settings
3. Monitor terminal performance metrics
4. Consider hardware upgrades if needed

### Logging and Monitoring

#### Enable Debug Logging
```python
# Add to Odoo configuration
log_level = debug
log_handler = :DEBUG
```

#### Monitor Performance
- Use the terminal status component for real-time monitoring
- Check performance metrics in Geidea Payment > Payment Transactions
- Review transaction logs for patterns and issues

### Support Contacts

- **Technical Support**: Contact your Geidea integration specialist
- **Documentation**: Refer to Geidea API documentation
- **Module Issues**: Submit issues through your Odoo support channel

## Migration and Upgrades

### Upgrading from Previous Versions
1. Backup your database before upgrading
2. Test the upgrade in a staging environment
3. Update module dependencies
4. Run database migration scripts if provided
5. Test all payment functionality after upgrade

### Data Migration
- Existing payment data is preserved during upgrades
- Transaction history remains accessible
- Terminal configurations are maintained
- New features are enabled with default settings

## Best Practices

### Configuration
- Use test environment for initial setup and testing
- Configure appropriate timeout values for your network
- Set reasonable retry limits to avoid excessive API calls
- Monitor connection pool utilization and adjust as needed

### Operations
- Regularly test terminal connectivity
- Monitor transaction success rates
- Review error logs for recurring issues
- Implement proper backup and recovery procedures

### Security
- Rotate API keys regularly
- Monitor access logs for suspicious activity
- Implement proper user access controls
- Keep encryption keys secure and backed up

## Changelog

### Version 1.1.0
- Added comprehensive Geidea payment integration
- Implemented multi-terminal support
- Added partial payment capabilities
- Enhanced security with encryption
- Added performance monitoring
- Improved error handling and recovery

### Version 1.0.0
- Initial Bonat loyalty system release
- Basic POS integration
- Customer engagement features

---

For additional support and documentation, please refer to the official Geidea API documentation and your Odoo administrator.