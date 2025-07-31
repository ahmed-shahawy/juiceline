# Geidea Payment Acquirer for Odoo 18

## Overview

This module provides comprehensive integration between Odoo 18 and Geidea payment gateway, specifically designed to address security, performance, and reliability issues in payment processing systems.

## Features

### Security Enhancements
- **Secure API Key Management**: All sensitive fields use `tracking=False` to prevent logging in audit trails
- **Protected Credentials**: API keys and merchant credentials are restricted to system administrators
- **Signature Verification**: Webhook signature validation for secure payment notifications

### Performance Improvements
- **Asynchronous Processing**: HTTP calls are non-blocking to prevent system freezing
- **Proper Datetime Handling**: Uses `fields.Datetime.now()` instead of `request.env.cr.now()`
- **Optimized POS Integration**: Safe model loading with existence checks

### Reliability Features
- **Comprehensive Error Handling**: Structured error responses in JSON format
- **Transaction Tracking**: Complete payment lifecycle management
- **Retry Mechanisms**: Built-in retry logic for failed API calls
- **Timeout Management**: Configurable API timeouts

### POS Integration
- **Safe Model Access**: Prevents crashes from missing model assumptions
- **Transaction ID Management**: Implements missing `set_geidea_transaction_id` method
- **Multi-platform Support**: Compatible with Windows, iPad, and Android POS systems

## Installation

1. Copy the module to your Odoo addons directory:
   ```bash
   cp -r payment_geidea_18 /path/to/odoo/addons/
   ```

2. Update the addons list:
   ```bash
   ./odoo-bin -u base -d your_database
   ```

3. Install the module through Odoo interface:
   - Go to Apps
   - Search for "Geidea Payment Acquirer"
   - Click Install

## Configuration

### Payment Provider Setup

1. Navigate to **Accounting > Configuration > Payment Providers**
2. Create a new provider or edit existing Geidea provider
3. Configure the following fields:
   - **Merchant ID**: Your Geidea merchant identifier
   - **Public Key**: API public key from Geidea
   - **Private Key**: API private key from Geidea
   - **Gateway URL**: Geidea API endpoint
   - **Test Mode**: Enable for testing, disable for production
   - **Currency Code**: Default currency (SAR, USD, EUR, etc.)
   - **Timeout**: API request timeout in seconds

### Geidea Acquirer Configuration

1. Navigate to **Accounting > Configuration > Geidea Acquirers**
2. Create a new acquirer configuration:
   - **Name**: Descriptive name for the configuration
   - **Company**: Associated company
   - **Payment Provider**: Link to payment provider
   - **Merchant ID**: Geidea merchant ID
   - **Terminal ID**: Terminal ID for POS transactions
   - **API Key**: Authentication key
   - **API Password**: Authentication password
   - **Gateway URL**: API endpoint URL
   - **Test Mode**: Enable for development/testing

### POS Configuration

1. Navigate to **Point of Sale > Configuration > Point of Sale**
2. Edit your POS configuration
3. In the Payment section, add Geidea as a payment method
4. Associate with the appropriate Geidea acquirer

## Usage

### E-commerce Payments

Customers can pay using credit/debit cards through the Geidea payment form. The integration handles:
- Card number validation and formatting
- Secure data transmission to Geidea
- Real-time payment status updates
- Automatic order confirmation

### POS Payments

In Point of Sale:
1. Add products to the order
2. Click "Payment"
3. Select Geidea payment method
4. Process payment through integrated terminal
5. Receive immediate confirmation

### Payment Management

- View all transactions in **Accounting > Payments > Transactions**
- Monitor payment status and details
- Process refunds when necessary
- Generate payment reports

## API Endpoints

### Webhook Endpoint
```
POST /payment/geidea/webhook
```
Receives payment notifications from Geidea gateway.

### Return Endpoint
```
GET/POST /payment/geidea/return
```
Handles customer return from payment page.

### Transaction Status
```
POST /api/geidea/transaction/status
```
Check payment transaction status.

### Refund Processing
```
POST /api/geidea/refund
```
Process payment refunds.

## Security Considerations

1. **Credential Protection**: All API keys are encrypted and access-controlled
2. **Audit Trail Security**: Sensitive data is not logged in system audit trails
3. **Webhook Security**: Implement signature verification for webhook authenticity
4. **SSL/TLS**: Ensure all API communications use HTTPS
5. **PCI Compliance**: Follow PCI DSS guidelines for card data handling

## Error Handling

The module provides comprehensive error handling:

- **API Errors**: Structured JSON responses with error codes
- **Network Timeouts**: Configurable timeout with retry logic
- **Validation Errors**: Clear error messages for invalid data
- **System Errors**: Graceful degradation and error logging

## Troubleshooting

### Common Issues

1. **Payment Fails with "Invalid Merchant ID"**
   - Verify merchant ID in provider configuration
   - Ensure test/production mode matches credentials

2. **POS Integration Not Working**
   - Check Geidea acquirer is assigned to POS configuration
   - Verify acquirer is active and POS-enabled

3. **Webhook Not Receiving Data**
   - Confirm webhook URL is accessible from internet
   - Check firewall and SSL certificate

4. **API Timeouts**
   - Increase timeout value in acquirer settings
   - Check network connectivity to Geidea servers

### Debugging

Enable debug logging by:
1. Adding logger configuration in Odoo
2. Setting log level to DEBUG for `payment_geidea_18`
3. Monitor logs for detailed API interactions

## Support

For technical support:
- Check Odoo logs for error details
- Verify Geidea API documentation
- Contact Geidea technical support for gateway issues

## License

This module is licensed under LGPL-3. See the LICENSE file for details.

## Contributors

- Odoo SA (Original framework)
- Community contributors (Enhancements and fixes)

## Changelog

### Version 18.0.1.0.0
- Initial release for Odoo 18
- Security fixes for sensitive data logging
- Asynchronous payment processing
- Comprehensive POS integration
- JSON-formatted API responses
- Multi-platform POS support
- Enhanced error handling and logging