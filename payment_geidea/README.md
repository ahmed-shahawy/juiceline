# Geidea Payment Module for Odoo 18

This module provides Geidea payment integration for Odoo 18.

## Problem Solved

This module addresses the error encountered when installing the Geidea payment module in Odoo 18:

```
ValueError: ValueError('External ID not found in the system: payment.payment_icon_cc_visa') while evaluating
"[(6, 0, [ref('payment.payment_icon_cc_visa'), ref('payment.payment_icon_cc_mastercard')])]"
```

## Solution

The issue was caused by references to payment icons that don't exist in Odoo 18 or have been moved/renamed. This module:

1. Creates a proper Geidea payment provider for Odoo 18
2. Removes the problematic external ID references to payment icons
3. Provides a clean, installable payment module structure

## Features

- Compatible with Odoo 18
- Supports credit card payments
- Tokenization support
- Configurable capture settings

## Installation

1. Copy the `payment_geidea` folder to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "Geidea Payment Acquirer" module

## Configuration

After installation, go to:
1. Accounting/Invoicing → Configuration → Payment Providers
2. Find "Geidea" in the list
3. Configure your Geidea credentials and settings

## Notes

- Payment icons have been temporarily removed to ensure compatibility
- To add payment icons back, you can:
  1. Check the file `data/payment_provider_data_with_icons.xml` for alternative approaches
  2. Try different external ID patterns like `payment.payment_icon_visa` (without 'cc_')
  3. Create your own payment icons within the module
  4. Use the alternative XML file by replacing the content of `payment_provider_data.xml`
- The module is created in disabled state by default for security
- This solution addresses the specific error: `ValueError('External ID not found in the system: payment.payment_icon_cc_visa')`

## Troubleshooting

If you still encounter external ID errors:
1. Check what payment icons exist in your Odoo 18 installation
2. Use the Odoo developer mode to inspect existing payment modules
3. Modify the external ID references accordingly
4. Consider creating custom payment icons instead of relying on system ones