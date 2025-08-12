# -*- coding: utf-8 -*-
{
    'name': 'Multi UOM Supplier',
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Support multiple units of measure for suppliers',
    'description': """
Multi UOM Supplier Module
=========================

This module extends Odoo's supplier functionality to support different units of measure 
for the same product from different suppliers.

Features:
- Add UOM field to supplier info (product.supplierinfo)
- Automatic UOM conversion in purchase orders
- Proper cost calculation based on supplier UOM
- Enhanced UI to manage supplier-specific UOMs

Technical Implementation:
- Extends product.supplierinfo model
- Extends purchase.order.line model  
- Updates product views for UOM management
""",
    'author': 'Juiceline',
    'depends': ['purchase', 'product', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}