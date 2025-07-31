# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Provider',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: Geidea',
    'description': """
Geidea Payment Provider
======================

This module provides integration with Geidea payment gateway for Odoo 18.
    """,
    'author': 'Ahmed Shahawy',
    'website': 'https://github.com/ahmed-shahawy/juiceline',
    'depends': ['payment'],
    'data': [
        'views/payment_geidea_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}