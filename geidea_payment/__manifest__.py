# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Gateway',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Geidea Payment Gateway Integration for Odoo',
    'description': """
Geidea Payment Gateway Integration
==================================

This module integrates Geidea payment gateway with Odoo, providing:

* Online payment processing through Geidea
* POS integration for card payments
* Secure transaction handling
* Real-time payment status updates
* Support for multiple currencies
* Comprehensive transaction logging

Features:
---------
* Seamless integration with Odoo's payment framework
* POS payment terminal support
* Webhook handling for payment notifications
* Transaction refund capabilities
* Multi-language support (Arabic/English)
* Comprehensive security and validation

Compatible with Odoo 18.0
    """,
    'author': 'Geidea Integration Team',
    'website': 'https://www.geidea.net',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'payment',
        'point_of_sale',
        'account',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_acquirer_data.xml',
        'views/payment_geidea_views.xml',
        'views/payment_transaction_views.xml',
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'geidea_payment/static/src/js/payment_form.js',
            'geidea_payment/static/src/css/geidea_payment.css',
        ],
        'point_of_sale._assets_pos': [
            'geidea_payment/static/src/js/pos_payment.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'external_dependencies': {
        'python': ['requests', 'hashlib', 'json'],
    },
    'price': 0.0,
    'currency': 'USD',
}