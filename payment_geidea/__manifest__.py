# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Geidea Payment Acquirer',
    'version': '1.0',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 365,
    'summary': 'Payment Acquirer: Geidea Implementation',
    'description': """Geidea Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}