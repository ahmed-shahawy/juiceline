# -*- coding: utf-8 -*-
{
    'name': 'Bonat Loyalty & Geidea Payment Integration',
    'version': '18.0.1.1',
    'category': 'Sales/Point of Sale',
    'summary': 'Loyalty and Customer Engagement with Geidea Payment Integration',
    'description': '''
    A comprehensive POS module that combines:
    - Bonat loyalty system for customer engagement and rewards
    - Advanced Geidea payment terminal integration with:
      * Robust terminal connection management
      * Multiple payment methods (card, contactless, mobile, QR)
      * Partial payments and refunds support
      * Real-time transaction monitoring
      * Enhanced security and encryption
      * Performance optimization and connection pooling
      * Comprehensive error handling and recovery
    ''',
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/geidea_payment_views.xml'
    ],
    'depends': ['point_of_sale', 'pos_discount'],
    'external_dependencies': {
        'python': ['requests', 'cryptography']
    },
    'installable': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_bonat_loyalty/static/src/**/*'
        ],
    },
    "author": "Bonat & Geidea Integration Team",
    'license': 'OPL-1',
}
