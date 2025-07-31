# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Provider',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Geidea',
    'description': """
Geidea Payment Provider
=======================

This module allows customers to pay using Geidea payment gateway.
Compatible with Odoo 18.
    """,
    'depends': ['payment'],
    'data': [
        'data/payment_provider_data.xml',
    ],
    'assets': {},
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}