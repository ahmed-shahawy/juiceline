{
    'name': 'Geidea Payment Gateway',
    'version': '18.0.1.0.0',
    'summary': 'Integrate Geidea POS with Odoo POS 18',
    'description': '''
        Geidea Payment Gateway Integration for Odoo POS 18

        This module provides integration with Geidea payment systems for 
        Odoo Point of Sale. It includes:
        - Payment method configuration
        - POS interface integration
        - Transaction processing simulation
        - Error handling and validation
    ''',
    'category': 'Point of Sale',
    'author': 'Custom Development',
    'website': 'https://geidea.net',
    'license': 'LGPL-3',
    # يجب تضمين كلا من 'point_of_sale' و 'payment' هنا:
    # - 'payment': حتى يكون payment.acquirer متاحاً (يلزم لتحميل بيانات الدفع)
    # - 'point_of_sale': حتى تتكامل الوحدة مع نقطة البيع
    'depends': [
        'point_of_sale',
        'payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_method_data.xml',   # تأكد أن هذا الملف يعرف فعلاً payment.acquirer أو payment.method
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
