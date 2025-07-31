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

1. **Simplified View Inheritance**: Removed redundant fallback view records that were causing conflicts. Uses a single, clean inheritance approach.

2. **Optimized XPath Strategy**: Instead of searching for potentially missing elements like `group[@name='provider_details']`, the solution uses `<group position="after">` which is more universal and works with most Odoo form structures.

3. **Odoo 18 Compatible Syntax**: Uses modern field attributes and follows Odoo 18 best practices for payment provider modules.

4. **Minimal Changes Approach**: The fix eliminates the dual-approach complexity and focuses on a single, robust solution.

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

## Key Improvements from Original
- **Single view inheritance record** instead of dual approach
- **Simplified XPath expression** for better compatibility
- **Cleaner code structure** with fewer potential conflicts
- **Better maintainability** for future Odoo versions

## Compatibility
- Odoo 18.0+
- Depends on: `payment` module

## Support
This module addresses the specific XPath errors encountered with Odoo 18 and provides a stable payment integration solution.