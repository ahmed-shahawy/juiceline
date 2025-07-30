# Geidea Payment Gateway for Odoo 18

## Overview

This module provides integration between Geidea payment systems and Odoo Point of Sale (POS) 18. It allows businesses to process payments through Geidea's payment gateway directly from the Odoo POS interface.

## Features

- **Payment Method Configuration**: Configure Geidea payment methods with merchant ID, terminal ID, and API keys
- **POS Integration**: Seamless integration with Odoo POS 18 interface
- **Transaction Tracking**: Complete transaction history and status tracking
- **Error Handling**: Comprehensive error handling and user feedback
- **Test Mode**: Support for test and production modes
- **Receipt Integration**: Geidea transaction details on receipts

## Installation

1. Copy the `geidea_payment` folder to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the "Geidea Payment Gateway" module from the Apps menu

## Configuration

1. Go to **Point of Sale > Configuration > Payment Methods**
2. Create a new payment method or edit an existing one
3. Enable "Use Geidea Payment"
4. Configure the following fields:
   - **Geidea Merchant ID**: Your merchant ID from Geidea
   - **Geidea Terminal ID**: Your terminal ID from Geidea
   - **Geidea API Key**: Your API key from Geidea
   - **Test Mode**: Enable for testing, disable for production

## Usage

1. Configure your POS to use the Geidea payment method
2. In the POS interface, select the Geidea payment method
3. Enter the payment amount
4. Process the payment through Geidea's system
5. The transaction status will be displayed and recorded

## Technical Details

### Models

- **pos.payment.method**: Extended to include Geidea configuration
- **geidea.payment**: New model for tracking Geidea transactions

### JavaScript Integration

- **GeideaPaymentInterface**: Payment interface for POS
- **Payment processing simulation**: For demonstration purposes
- **Transaction tracking**: Real-time status updates

### Views

- Payment method configuration forms
- Transaction management views
- POS interface templates

### Security

- Access rights for POS users and managers
- Secure API key storage

## Testing

The module includes comprehensive tests for:

- Payment method configuration validation
- Transaction processing
- Error handling
- State management

Run tests with:
```bash
odoo-bin -d <database> -i geidea_payment --test-enable --stop-after-init
```

## Requirements

- Odoo 18.0
- point_of_sale module
- payment module

## Support

For support and issues, please contact the module developer or refer to the Geidea payment gateway documentation.

## License

LGPL-3

---

**Note**: This module includes simulated payment processing for demonstration purposes. In a production environment, you would need to integrate with Geidea's actual API endpoints.