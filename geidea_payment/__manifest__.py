{
    'name': 'Geidea Payment Gateway',
    'version': '18.0.1.0.0',
    'summary': 'Integrate Geidea POS with Odoo POS 18',
    'description': """
        Geidea Payment Gateway Integration for Odoo POS 18
        
        This module provides integration with Geidea payment systems for 
        Odoo Point of Sale. It includes:
        - Payment method configuration
        - POS interface integration
        - Transaction processing simulation
        - Error handling and validation
    """,
    'category': 'Point of Sale',
    'author': 'Custom Development',
    'website': 'https://geidea.net',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_method_data.xml',
        'views/pos_payment_method_views.xml',
        'views/geidea_payment_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'geidea_payment/static/src/js/geidea_payment.js',
            'geidea_payment/static/src/xml/geidea_payment.xml',
            'geidea_payment/static/src/css/geidea_payment.css',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}