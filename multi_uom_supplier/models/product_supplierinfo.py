# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    supplier_uom = fields.Many2one(
        'uom.uom', 
        string='Supplier Unit of Measure',
        help="Unit of measure used by this supplier for this product. "
             "If not set, the product's purchase UOM will be used."
    )
    
    # Helper field for domain filtering in views
    product_uom_category_id = fields.Many2one(
        related='product_tmpl_id.uom_po_id.category_id',
        string='Product UOM Category',
        store=False
    )

    @api.constrains('supplier_uom', 'product_tmpl_id', 'product_id')
    def _check_supplier_uom_category(self):
        """Ensure supplier UOM is compatible with product UOM"""
        for record in self:
            if record.supplier_uom:
                product = record.product_id or record.product_tmpl_id
                if product and product.uom_po_id:
                    if record.supplier_uom.category_id != product.uom_po_id.category_id:
                        raise ValidationError(_(
                            "The supplier unit of measure '%s' is not compatible with "
                            "the product's purchase unit of measure '%s'. "
                            "They must belong to the same UOM category."
                        ) % (record.supplier_uom.name, product.uom_po_id.name))

    def _get_supplier_uom(self):
        """Get the UOM used by this supplier, fallback to product's purchase UOM"""
        self.ensure_one()
        if self.supplier_uom:
            return self.supplier_uom
        
        product = self.product_id or self.product_tmpl_id
        return product.uom_po_id if product else False

    def _convert_price_to_product_uom(self, price):
        """Convert supplier price from supplier UOM to product's purchase UOM"""
        self.ensure_one()
        if not self.supplier_uom:
            return price
            
        product = self.product_id or self.product_tmpl_id
        if not product or not product.uom_po_id:
            return price
            
        # Convert price from supplier UOM to product UOM
        if self.supplier_uom != product.uom_po_id:
            # Price per supplier UOM -> Price per product UOM
            # If supplier sells 1 KG for 10$, and product UOM is 1000g
            # Then price per product UOM should be 10$ (same price for same quantity)
            return self.supplier_uom._compute_price(price, product.uom_po_id)
        
        return price

    def _convert_price_from_product_uom(self, price):
        """Convert price from product's purchase UOM to supplier UOM"""
        self.ensure_one()
        if not self.supplier_uom:
            return price
            
        product = self.product_id or self.product_tmpl_id
        if not product or not product.uom_po_id:
            return price
            
        # Convert price from product UOM to supplier UOM
        if self.supplier_uom != product.uom_po_id:
            return product.uom_po_id._compute_price(price, self.supplier_uom)
        
        return price