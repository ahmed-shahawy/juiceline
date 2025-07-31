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
- Icons can be added back once the correct external IDs for Odoo 18 are identified
- The module is created in disabled state by default for security