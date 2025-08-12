# -*- coding: utf-8 -*-
{
    'name': 'Supplier Unit of Measurement',
    'version': '1.0.0',
    'category': 'Purchase',
    'summary': 'Manage supplier-specific units of measurement',
    'description': """
        This module allows managing supplier-specific units of measurement
        to handle different UOMs from suppliers.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'purchase',
        'uom',
    ],
    'data': [
        'views/supplier_uom_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}