# -*- coding: utf-8 -*-
{
    'name': 'Bonat Loyalty',
    'version': '18.0.1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Loyalty and Customer Engagement',
    'description': 'A customized loyalty system for your store: Promote your new products with ease by motivating your customers with rewards and customized offers, then retarget them with multiple marketing tools and make your decisions based on detailed reports.',
    'data': [
        'views/res_config_settings_view.xml',
        'views/product_template_view.xml'
    ],
    'depends': ['point_of_sale', 'pos_discount', 'uom', 'product'],
    'installable': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_bonat_loyalty/static/src/**/*'
        ],
    },
    "author": "Bonat",
    'license': 'OPL-1',
}
