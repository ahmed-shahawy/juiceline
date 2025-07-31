# Geidea Payment Provider for Odoo 18

## Overview
This module adds Geidea payment provider support to Odoo 18, addressing the issue where necessary merchant credential fields were missing from the payment provider configuration interface.

## Problem Solved
- **Issue**: Missing credential fields (Merchant ID, Terminal ID, API Key, API Secret) in Geidea payment provider UI
- **Solution**: Complete payment provider module with all required fields visible in the Credentials tab

## Features
- ✅ **Merchant ID** field - Required credential for Geidea merchant identification
- ✅ **Terminal ID** field - Required terminal identifier for payment processing  
- ✅ **API Key** field - Required API access key
- ✅ **API Secret** field - Required API secret key (password protected)
- ✅ **Environment** selection - Choose between Test and Production environments
- ✅ **Secure UI** - All sensitive fields use password input type
- ✅ **Conditional Display** - Fields only appear when "geidea" provider is selected
- ✅ **Validation** - All fields are required when using Geidea provider

## Installation

1. Copy the `payment_geidea` module to your Odoo addons directory
2. Update your addons list: `Apps > Update Apps List`
3. Install the module: `Apps > Search "Geidea" > Install`

## Configuration

1. Go to `Invoicing > Configuration > Payment Providers`
2. Create a new payment provider or edit existing Geidea provider
3. Set **Code** to "geidea"
4. Go to the **Credentials** tab
5. Fill in your Geidea merchant credentials:
   - Merchant ID
   - Terminal ID
   - API Key
   - API Secret
   - Environment (Test/Production)

## Technical Details

### Module Structure
```
payment_geidea/
├── __manifest__.py              # Module manifest
├── __init__.py                  # Module initialization
├── models/
│   ├── __init__.py
│   ├── payment_provider.py     # Extended payment.provider model
│   └── payment_transaction.py  # Payment transaction handling
├── views/
│   ├── payment_provider_views.xml    # UI views for credentials
│   └── payment_geidea_templates.xml  # Payment form templates
├── controllers/
│   ├── __init__.py
│   └── main.py                 # Payment processing controllers
└── data/
    └── payment_provider_data.xml     # Default provider configuration
```

### Model Extensions
The module extends the `payment.provider` model with Geidea-specific fields:
- `geidea_merchant_id` - Char field for Merchant ID
- `geidea_terminal_id` - Char field for Terminal ID  
- `geidea_api_key` - Char field for API Key
- `geidea_api_secret` - Char field for API Secret
- `geidea_environment` - Selection field (test/production)

### View Integration
The credentials fields are added to the existing payment provider form view and are only visible when the provider code is set to "geidea".

## Compliance
- ✅ Follows Odoo 18 module development standards
- ✅ Uses proper field validation and security
- ✅ Implements minimal code changes approach
- ✅ Compatible with existing payment provider infrastructure

## Support
This module addresses the specific requirement of adding missing credential fields to the Geidea payment provider configuration in Odoo 18.