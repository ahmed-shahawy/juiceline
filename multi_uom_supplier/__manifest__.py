# -*- coding: utf-8 -*-
{
    'name': 'Multi UOM Supplier',
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Multiple Units of Measure for Suppliers',
    'description': """
Multi UOM Supplier Module
=========================

This module allows setting different units of measure for the same product 
from different suppliers. Features include:

* Supplier-specific UOM for each product
* Automatic UOM conversion in purchase orders
* Proper cost calculation based on supplier UOM
* Enhanced supplier information management

Key Benefits:
* Handle suppliers selling same products in different UOMs
* Automatic conversion between UOMs during purchase
* Accurate pricing and cost calculations
* Improved purchase order management
    """,
    'author': 'Ahmed Shahawy',
    'website': 'https://github.com/ahmed-shahawy/juiceline',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'purchase',
        'uom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_supplierinfo_views.xml',
        'views/purchase_order_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}