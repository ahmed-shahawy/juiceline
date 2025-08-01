# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Provider',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Geidea Implementation',
    'description': """
Geidea Payment Provider
=======================

This module integrates Geidea payment gateway with Odoo, providing:
- Secure payment processing through Geidea API
- Support for online payments and Point of Sale integration
- Tokenization for recurring payments
- Express checkout functionality
- Full compliance with Odoo 18 payment provider structure
    """,
    'author': 'Juiceline',
    'website': 'https://www.geidea.net/',
    'depends': [
        'payment',
        'point_of_sale',
    ],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_geidea_templates.xml',
        'views/payment_provider_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_geidea/static/src/js/payment_form.js',
        ],
        'point_of_sale._assets_pos': [
            'payment_geidea/static/src/js/pos_integration.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}