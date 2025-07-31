# Geidea Payment Provider for Odoo 18

## Overview
This module integrates Geidea payment gateway with Odoo 18, providing a complete payment solution for Middle Eastern markets.

## Problem Solved
The original module was encountering this XPath error during installation:
```
Element '<xpath expr="//group[@name='provider_details']">' cannot be located in parent view
```

## Solution Implemented
This version fixes the XPath compatibility issues by:

1. **Using Reliable Anchor Points**: Instead of searching for `group[@name='provider_details']`, we use `field[@name='code']` which is guaranteed to exist in payment provider forms.

2. **Multiple Fallback Approaches**: 
   - Primary: Add fields after the `code` field
   - Fallback: Add fields at the end of the form if the primary approach fails

3. **Odoo 18 Compatible Syntax**: Uses modern field attributes instead of deprecated `attrs` syntax.

## Installation
1. Copy this module to your Odoo addons directory
2. Update the module list in Odoo
3. Install the "Geidea Payment Provider" module

## Configuration
1. Go to Accounting > Configuration > Payment Providers
2. Find "Geidea" in the list and configure:
   - Merchant Key
   - Merchant Password
   - Merchant Public Key
3. Set the provider state to "Enabled" or "Test Mode"

## Features
- Full integration with Odoo 18 payment system
- Support for AED, USD, EUR, SAR, EGP currencies
- Secure credential management
- Transaction tracking and management
- Webhook support for real-time payment updates

## Technical Details
- **Models**: Extends `payment.provider` and `payment.transaction`
- **Views**: Compatible payment provider configuration forms
- **Controllers**: Handles payment flow and webhooks
- **Security**: Proper field-level security for sensitive data

## Compatibility
- Odoo 18.0+
- Depends on: `payment` module

## Support
This module addresses the specific XPath errors encountered with Odoo 18 and provides a stable payment integration solution.