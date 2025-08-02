# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Integrate Geidea payment devices with Odoo POS',
    'description': '''
        Comprehensive Geidea Payment Integration Module for Odoo 18
        
        Features:
        - Multi-platform support (Windows, iPad, Android)
        - Geidea device management
        - Secure API key management
        - Real-time transaction processing
        - POS integration
        - Transaction monitoring and reporting
        
        Configuration:
        - API Key management
        - Merchant ID configuration
        - Terminal ID setup
        - Device registration and management
    ''',
    'author': 'Juiceline',
    'website': 'https://github.com/ahmed-shahawy/juiceline',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'point_of_sale',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/geidea_payment_method_data.xml',
        'views/geidea_config_views.xml',
        'views/geidea_device_views.xml',
        'views/geidea_transaction_views.xml',
        'views/res_config_settings_views.xml',
        'views/geidea_menu_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_geidea_payment/static/src/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}