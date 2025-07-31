# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Provider',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Geidea Implementation',
    'description': """
Geidea Payment Provider
=======================

This module implements Geidea payment provider for Odoo 18.
It allows you to process payments through Geidea payment gateway.

Features:
- Support for Geidea payment gateway integration
- Configurable merchant credentials
- Test and production environment support
    """,
    'depends': ['payment'],
    'data': [
        'views/payment_geidea_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'author': 'Juiceline',
}