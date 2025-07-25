# -*- coding: utf-8 -*-
{
    'name': 'Geidea POS Payment Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'iPad-optimized Geidea payment integration for Odoo POS',
    'description': '''
        iPad-Optimized Geidea Payment Integration
        ========================================
        
        This module provides a comprehensive Geidea payment integration specifically 
        optimized for iPad and iOS devices within Odoo POS.
        
        Key Features:
        - Robust Bluetooth connection handling for iPad
        - iOS/iPadOS performance optimizations
        - iPad-specific UI/UX components
        - Secure payment processing with iOS Keychain integration
        - Power management and battery optimization
        - Background/foreground state handling
        - Multi-screen size support
        - Touch-optimized interface
        
        The module integrates seamlessly with existing POS workflows while providing
        enhanced functionality specifically designed for iPad devices.
    ''',
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'base',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
        'views/geidea_payment_views.xml',
        'data/geidea_payment_data.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_geidea_payment/static/src/css/geidea_payment.css',
            'pos_geidea_payment/static/src/js/models/geidea_payment_model.js',
            'pos_geidea_payment/static/src/js/bluetooth/geidea_bluetooth_manager.js',
            'pos_geidea_payment/static/src/js/bluetooth/ios_bluetooth_adapter.js',
            'pos_geidea_payment/static/src/js/security/ios_keychain_manager.js',
            'pos_geidea_payment/static/src/js/ui/geidea_payment_screen.js',
            'pos_geidea_payment/static/src/js/ui/geidea_connection_widget.js',
            'pos_geidea_payment/static/src/js/ui/geidea_payment_button.js',
            'pos_geidea_payment/static/src/js/power/ios_power_manager.js',
            'pos_geidea_payment/static/src/js/utils/geidea_utils.js',
            'pos_geidea_payment/static/src/xml/geidea_payment_templates.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}