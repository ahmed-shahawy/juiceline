# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Acquirer',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: Geidea Implementation',
    'description': '''
        This module integrates Geidea payment gateway with Odoo 18.
        Features:
        - Secure API key management
        - Asynchronous payment processing
        - POS integration with transaction tracking
        - Comprehensive error handling
        - REST API endpoints with JSON responses
        - Multi-platform support (Windows, iPad, Android)
    ''',
    'author': 'Odoo SA',
    'website': 'https://www.odoo.com',
    'depends': ['payment', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_geidea_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'payment_geidea_18/static/src/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}