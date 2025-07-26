# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Integration',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: Geidea Implementation for cross-platform POS systems',
    'description': '''
        Geidea Payment Integration for Odoo 18
        =====================================
        
        This module provides comprehensive integration with Geidea payment devices
        supporting multiple platforms:
        - Windows: USB/Serial and Network API connections
        - iPad: Bluetooth and Lightning/USB-C connections  
        - Android: USB OTG and Bluetooth connections
        
        Features:
        - Multi-platform device support
        - Real-time payment processing
        - Secure transaction handling with PCI DSS compliance
        - Support for contactless payments (NFC)
        - Digital wallet support (Apple Pay, Google Pay)
        - Comprehensive reporting and analytics
    ''',
    'author': 'Ahmed Shahawy',
    'website': 'https://github.com/ahmed-shahawy/juiceline',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'payment',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_acquirer_views.xml',
        'views/geidea_device_views.xml',
        'views/geidea_transaction_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'geidea_payment/static/src/js/**/*',
            'geidea_payment/static/src/css/**/*',
        ],
        'web.assets_backend': [
            'geidea_payment/static/src/js/backend/**/*',
            'geidea_payment/static/src/css/backend/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'external_dependencies': {
        'python': ['pyserial', 'websockets', 'cryptography'],
    },
}