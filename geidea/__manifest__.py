# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Integration',
    'version': '18.0.1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Geidea Payment Device Integration for POS',
    'description': '''
        This module provides integration with Geidea payment devices for Odoo Point of Sale.
        Features:
        - Configure Geidea payment acquirer settings
        - Process payments through Geidea devices
        - POS frontend integration for seamless payment processing
        - API endpoints for frontend communication
    ''',
    'author': 'Juiceline',
    'license': 'OPL-1',
    'depends': [
        'point_of_sale',
        'payment'
    ],
    'data': [
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'views/geidea_payment_acquirer.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'geidea/static/src/js/geidea_pos.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}