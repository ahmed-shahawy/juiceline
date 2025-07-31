# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Provider',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Geidea',
    'description': """
Geidea Payment Provider
=======================

This module integrates Geidea payment gateway with Odoo 18.
    """,
    'depends': ['payment'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_geidea_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}