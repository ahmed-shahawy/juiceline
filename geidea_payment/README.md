# Geidea Payment Module

## Overview
This module integrates Geidea payment processing system with Odoo, providing secure payment processing capabilities for multiple devices (Windows, iPad, Android).

## Features
- ✅ **Currency Provider Fix**: Properly handles currency_provider field without warnings
- ✅ **App Installation**: Module appears in Odoo Apps for easy installation
- ✅ **Secure Credentials**: Safe storage of API keys and merchant information
- ✅ **Test Mode Support**: Development and production environments
- ✅ **Multi-Device Support**: Works across different platforms

## Installation

### Step 1: Install Module
1. Copy the `geidea_payment` folder to your Odoo addons directory
2. Update your Apps list in Odoo
3. Search for "Geidea Payment Module" in Apps
4. Click Install

### Step 2: Configuration
1. Go to **Settings > General Settings**
2. Scroll down to **Geidea Payment Configuration** section
3. Configure the following:
   - **Test Mode**: Enable for development/testing
   - **Merchant ID**: Your Geidea merchant identifier
   - **API Key**: Your Geidea API authentication key

### Step 3: Payment Provider Setup
1. Go to **Accounting > Configuration > Payment Providers**
2. Find the **Geidea** provider
3. Configure:
   - Set state to "Enabled"
   - Enter your credentials
   - Configure payment methods
   - Set up webhook URLs

## Technical Details

### Fixed Issues
- **Currency Provider Warning**: Removed selection attribute from related currency_provider field
- **Module Visibility**: Added `application: True` in manifest for Apps visibility
- **Proper Dependencies**: Includes base, payment, and account modules

### File Structure
```
geidea_payment/
├── __manifest__.py          # Module configuration
├── models/
│   ├── res_config_settings.py    # Settings configuration
│   └── payment_acquirer.py       # Payment provider logic
├── views/
│   ├── res_config_settings_views.xml  # Settings UI
│   └── payment_acquirer_views.xml     # Provider UI
├── data/
│   └── payment_acquirer_data.xml      # Default provider data
├── security/
│   └── ir.model.access.csv           # Access control
└── controllers/
    └── main.py                       # Payment processing endpoints
```

### API Integration
The module integrates with Geidea's payment API:
- **Sandbox**: `https://api-sandbox.geidea.net`
- **Production**: `https://api.geidea.net`

### Security
- API keys are stored securely with password field type
- Access control rules protect sensitive payment data
- Test mode prevents accidental production charges

## Troubleshooting

### Module Not Appearing in Apps
- Ensure `application: True` is set in `__manifest__.py`
- Check that all dependencies are installed
- Update Apps list after copying files

### Currency Provider Warnings
- Verify that related fields don't have selection attributes
- Check Odoo logs for specific field warnings
- Restart Odoo server after module updates

### Payment Processing Issues
- Verify API credentials are correct
- Check test mode vs production mode settings
- Review Odoo logs for API request errors

## Support
For technical support, check:
- Odoo logs for detailed error messages
- Geidea API documentation
- Module security and access permissions