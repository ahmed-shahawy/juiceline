# -*- coding: utf-8 -*-
{
    'name': 'Geidea Payment Module',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment',
    'summary': 'Geidea Payment Integration for Odoo',
    'description': """
        Integration with Geidea payment processing system
        - Support for multiple devices (Windows, iPad, Android)
        - Secure credential management
        - Real-time transaction processing
        - Currency provider configuration
    """,
    'author': 'Geidea Payment Solutions',
    'website': 'https://geidea.net',
    'license': 'LGPL-3',
    'depends': ['base', 'payment', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_acquirer_views.xml',
        'views/res_config_settings_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,  # Makes the module appear as an app
}