# Juiceline - Odoo Modules Collection

This repository contains specialized Odoo modules for various business needs.

## Modules

### 🔶 Geidea Payment Gateway (`geidea_payment`)
**Branch: Geidea-Payment**

A comprehensive payment gateway integration module for Odoo 18 that provides:

- **Online Payment Processing**: Secure web-based payments through Geidea gateway
- **POS Terminal Integration**: Direct card payment processing for point-of-sale
- **Multi-Currency Support**: Accept payments in various currencies  
- **Webhook Integration**: Real-time payment status updates
- **Refund Management**: Process partial and full refunds
- **Professional UI**: Clean, responsive payment interface
- **Security Features**: HMAC signature validation and SSL encryption

**Key Features:**
- Odoo 18 compatible
- Arabic/English language support
- Comprehensive transaction tracking
- Email notifications
- Admin configuration interface
- Error handling and logging

**Installation:**
```bash
git checkout Geidea-Payment
cp -r geidea_payment /path/to/odoo/addons/
```

See `geidea_payment/README.md` for detailed documentation.

---

### 🔸 POS Bonat Loyalty (`pos_bonat_loyalty_18 v2`)

Loyalty and customer engagement system for point-of-sale operations.

---

## Development

Each module is maintained on its own branch for better organization and version control.

## License

Individual modules may have different licenses. Check each module's manifest file for specific licensing information.