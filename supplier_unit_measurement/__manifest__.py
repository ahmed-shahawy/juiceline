# -*- coding: utf-8 -*-
{
    'name': 'مديول تحديد وحدة قياس الشراء للموردين',
    'version': '18.0.1.0',
    'category': 'Purchase',
    'summary': 'إدارة وحدات القياس المختلفة للموردين',
    'description': '''
        مديول لإدارة وحدات القياس للموردين يتيح:
        - إدارة وحدات القياس المختلفة
        - ربط وحدات القياس بالموردين
        - تحويل الكميات بين وحدات القياس المختلفة
        - تطبيق وحدة القياس الصحيحة تلقائياً عند إنشاء طلبات الشراء
    ''',
    'depends': ['base', 'purchase', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'views/supplier_uom_views.xml',
        'views/uom_conversion_views.xml',
        'views/res_partner_views.xml',
        'data/uom_conversion_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'supplier_unit_measurement/static/src/js/uom_converter.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'author': 'Ahmed Shahawy',
    'license': 'LGPL-3',
}