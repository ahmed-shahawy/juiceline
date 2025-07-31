# Geidea Payment Module - Odoo 18 Compatibility

## Problem Resolved

The original issue was:
```
ValueError: External ID not found in the system: payment.payment_icon_cc_visa
```

This error occurred because Odoo 18 changed the way payment icons are handled, and the old external IDs for payment icons (`payment.payment_icon_cc_visa`, `payment.payment_icon_cc_mastercard`) are no longer available.

## Solution Implemented

### 1. Removed Deprecated Payment Icon References

**Before (causing error):**
```xml
<field name="payment_icon_ids" eval="[(6, 0, [ref('payment.payment_icon_cc_visa'), ref('payment.payment_icon_cc_mastercard')])]"/>
```

**After (Odoo 18 compatible):**
```xml
<field name="payment_method_ids" eval="[(6, 0, [ref('payment.payment_method_card')])]"/>
```

### 2. Updated Payment Provider Structure

- Used `payment_method_ids` instead of deprecated `payment_icon_ids`
- Referenced standard `payment.payment_method_card` instead of specific icon external IDs
- Ensured all fields are compatible with Odoo 18's payment provider model

### 3. Modern Payment Provider Features

- Added support for tokenization (`allow_tokenization`)
- Proper currency support for Middle Eastern markets
- Compatible with Odoo 18's payment framework
- Added proper form views for configuration

### 4. Files Created

1. **`__manifest__.py`** - Module manifest with Odoo 18 compatibility
2. **`models/payment_provider.py`** - Extended payment provider model with Geidea-specific fields
3. **`models/payment_transaction.py`** - Transaction handling for Geidea payments
4. **`data/payment_provider_data.xml`** - Provider data without deprecated external IDs
5. **`views/payment_provider_views.xml`** - Configuration forms for Geidea credentials

### 5. Key Changes for Odoo 18 Compatibility

- **Payment Icons**: Removed references to `payment.payment_icon_cc_visa` and `payment.payment_icon_cc_mastercard`
- **Payment Methods**: Used standard `payment.payment_method_card` reference
- **Model Fields**: All fields compatible with Odoo 18 payment provider structure
- **Dependencies**: Only depends on core `payment` module
- **Version**: Set to `18.0.1.0.0` for proper Odoo 18 compatibility

## Installation

The module can now be installed in Odoo 18 without the ValueError related to missing payment icon external IDs.

## Configuration

After installation:
1. Go to Accounting → Configuration → Payment Providers
2. Find "Geidea" provider
3. Configure Merchant ID, API Key, and Merchant Password
4. Enable the provider and set to "Enabled" state