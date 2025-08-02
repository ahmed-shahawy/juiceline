# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Provider',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Geidea',
    'description': """
Geidea Payment Provider
======================

This module provides integration with Geidea payment gateway for Odoo 18.

Features:
- Complete Geidea payment provider integration
- Support for multiple payment devices (Windows, Android, iOS)
- Device management with multiple connection types (USB, Bluetooth, Network, etc.)
- Transaction tracking and monitoring
- Configurable security settings with PCI DSS compliance
- Multi-language support (Arabic and English)
- Comprehensive logging and error handling
- Webhook support for real-time payment notifications
- API endpoints for payment processing and device management

Requirements:
- Geidea API credentials (API Key, Merchant ID, Terminal ID)
- Compatible payment devices
- Valid SSL certificate for webhook notifications
    """,
    'author': 'Ahmed Shahawy',
    'website': 'https://github.com/ahmed-shahawy/juiceline',
    'depends': ['payment', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_geidea_templates.xml',
        'views/geidea_menus.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}