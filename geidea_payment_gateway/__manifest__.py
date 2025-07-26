# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Gateway',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Geidea Payment Gateway Integration for POS and eCommerce',
    'description': """
Geidea Payment Gateway Integration
==================================

This module provides complete integration with Geidea Payment Gateway supporting:

* POS and eCommerce payments
* Multi-platform support (Windows, iOS, Android)  
* PCI DSS security compliance
* Multi-currency support
* Real-time payment processing
* Comprehensive transaction management
* Epson printer integration for POS receipts

Features:
---------
* Secure payment processing
* Real-time transaction status updates
* Comprehensive error handling
* Multi-language support (Arabic/English)
* Complete audit trail
* Refund and partial refund support
    """,
    'author': 'Ahmed Shahawy',
    'website': 'https://www.geidea.net',
    'depends': [
        'base',
        'payment',
        'point_of_sale',
        'account',
        'sale',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_transaction_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'geidea_payment_gateway/static/src/js/**/*',
            'geidea_payment_gateway/static/src/css/**/*',
        ],
        'web.assets_frontend': [
            'geidea_payment_gateway/static/src/js/payment_form.js',
            'geidea_payment_gateway/static/src/css/payment_form.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'USD',
}