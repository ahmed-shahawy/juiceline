# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Terminal Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Cross-platform Geidea payment terminal integration for Odoo POS',
    'description': '''
        Geidea Payment Terminal Integration
        ===================================
        
        Cross-platform payment terminal integration for Geidea payment processing.
        
        Features:
        - Support for Windows, iOS/iPad, and Android platforms
        - Multiple connection types: USB, Bluetooth, Network
        - Automatic terminal discovery and reconnection
        - Real-time connection status monitoring
        - Platform-specific optimizations
        - Unified error handling and user feedback
    ''',
    'author': 'Juiceline',
    'license': 'OPL-1',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
        'views/geidea_terminal_views.xml',
        'data/payment_method_data.xml',
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