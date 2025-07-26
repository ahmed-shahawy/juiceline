# Geidea Payment Gateway Module

## Overview

The Geidea Payment Gateway module provides seamless integration between Odoo 18 and the Geidea payment platform. This module enables businesses to accept online payments and process POS transactions through Geidea's secure payment infrastructure.

## Features

### 🚀 Core Payment Processing
- **Online Payment Gateway**: Secure web-based payment processing
- **POS Terminal Integration**: Direct card payment processing through terminals
- **Multi-Currency Support**: Accept payments in multiple currencies
- **Real-time Processing**: Instant payment verification and status updates

### 🔐 Security & Compliance
- **HMAC Signature Validation**: Secure API communication
- **SSL/TLS Encryption**: All transactions encrypted in transit
- **PCI Compliance**: Follows payment card industry standards
- **Webhook Verification**: Secure payment notifications

### 📊 Transaction Management
- **Comprehensive Tracking**: Full transaction lifecycle monitoring
- **Refund Processing**: Partial and full refund capabilities
- **Status Monitoring**: Real-time payment status checking
- **Detailed Reporting**: Transaction history and analytics

### 🎨 User Experience
- **Responsive Design**: Mobile-friendly payment interface
- **Multi-language Support**: Arabic and English interface
- **Professional UI**: Clean, modern payment forms
- **Error Handling**: User-friendly error messages

## Installation

### Prerequisites
- Odoo 18.0 or higher
- Python 3.8+
- Active Geidea merchant account

### Installation Steps

1. **Download the Module**
   ```bash
   git clone https://github.com/ahmed-shahawy/juiceline.git
   cd juiceline
   git checkout Geidea-Payment
   ```

2. **Copy to Addons Directory**
   ```bash
   cp -r geidea_payment /path/to/odoo/addons/
   ```

3. **Update Apps List**
   - Go to Apps menu in Odoo
   - Click "Update Apps List"
   - Search for "Geidea Payment Gateway"

4. **Install the Module**
   - Click "Install" on the Geidea Payment Gateway module
   - Wait for installation to complete

## Configuration

### 1. Payment Acquirer Setup

Navigate to **Accounting > Configuration > Payment Acquirers**

1. Find "Geidea" in the list
2. Configure the following settings:
   - **Name**: Your preferred display name
   - **State**: Set to "Enabled" for production
   - **Merchant ID**: Your Geidea merchant ID
   - **Merchant Key**: Your Geidea merchant key
   - **API Password**: Your Geidea API password
   - **Gateway URL**: Production or sandbox URL

### 2. POS Configuration

Navigate to **Point of Sale > Configuration > Payment Methods**

1. Create a new payment method:
   - **Name**: "Geidea Card Payment"
   - **Use Payment Terminal**: Select "Geidea Payment Terminal"
   - **Terminal ID**: Your Geidea terminal ID
   - **Terminal Key**: Your terminal authentication key
   - **POS API URL**: Geidea POS API endpoint

### 3. Website Payment Configuration

Navigate to **Website > Configuration > Settings**

1. Enable website payments
2. Add Geidea as a payment acquirer
3. Configure display options and messaging

## Usage

### Online Payments

1. **Customer Experience**:
   - Customer selects Geidea payment method
   - Redirected to secure Geidea payment page
   - Completes payment with card details
   - Returns to merchant site with confirmation

2. **Merchant Dashboard**:
   - View all transactions in Payment Transactions menu
   - Monitor payment status in real-time
   - Process refunds when needed
   - Generate payment reports

### POS Payments

1. **Cashier Process**:
   - Select Geidea payment method in POS
   - Enter payment amount
   - Customer completes payment on terminal
   - Transaction automatically recorded

2. **Terminal Management**:
   - Test terminal connections
   - Monitor terminal status
   - Handle connection issues

## API Integration

### Webhook Endpoints

The module provides several webhook endpoints:

- `POST /payment/geidea/webhook` - Payment notifications
- `GET /payment/geidea/return` - Payment completion redirect
- `GET /payment/geidea/cancel` - Payment cancellation redirect

### POS API Endpoints

- `POST /payment/geidea/pos/initiate` - Start POS payment
- `POST /payment/geidea/pos/status` - Check payment status
- `POST /payment/geidea/pos/cancel` - Cancel POS payment

## Troubleshooting

### Common Issues

1. **Payment Failed Error**:
   - Check merchant credentials
   - Verify network connectivity
   - Review Geidea account status

2. **Terminal Connection Issues**:
   - Verify terminal ID and key
   - Check network connectivity
   - Restart terminal if needed

3. **Webhook Not Received**:
   - Check firewall settings
   - Verify webhook URL configuration
   - Review Geidea webhook settings

### Debug Mode

Enable debug logging by:
1. Going to Settings > Technical > Logging
2. Adding logger for `geidea_payment`
3. Setting log level to DEBUG

### Support Contacts

- **Geidea Technical Support**: [Geidea Support Portal]
- **Module Developer**: Available through GitHub issues
- **Odoo Community**: [Odoo Community Forum]

## Security Considerations

### Best Practices

1. **Credential Management**:
   - Store credentials securely
   - Use different keys for production/testing
   - Regularly rotate API keys

2. **Network Security**:
   - Use HTTPS for all communications
   - Implement proper firewall rules
   - Monitor for suspicious activity

3. **Data Protection**:
   - Never store card details
   - Comply with GDPR requirements
   - Regular security audits

### Compliance

This module helps maintain compliance with:
- PCI DSS standards
- GDPR data protection
- Regional payment regulations

## Development

### Module Structure

```
geidea_payment/
├── __manifest__.py          # Module definition
├── models/                  # Data models
│   ├── payment_acquirer.py
│   ├── payment_transaction.py
│   └── pos_payment_method.py
├── controllers/             # Web controllers
├── views/                   # XML views
├── static/                  # Frontend assets
├── security/               # Access rights
└── data/                   # Initial data
```

### Customization

The module can be extended by:
1. Inheriting from existing models
2. Adding custom fields and methods
3. Implementing additional payment features
4. Creating custom reports and dashboards

### Testing

Run module tests:
```bash
odoo-bin -i geidea_payment -d test_database --test-enable
```

## Changelog

### Version 18.0.1.0.0
- Initial release for Odoo 18
- Complete payment gateway integration
- POS terminal support
- Webhook handling
- Professional UI/UX

## License

This module is licensed under LGPL-3. See LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Consult Odoo community forums

---

*This documentation is maintained by the Geidea Payment Module development team.*