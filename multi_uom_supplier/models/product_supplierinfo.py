# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    supplier_uom_id = fields.Many2one(
        'uom.uom',
        string='Supplier UOM',
        help="Unit of measure used by this supplier for this product. "
             "If not specified, the product's purchase UOM will be used."
    )
    supplier_uom_factor = fields.Float(
        string='UOM Conversion Factor',
        compute='_compute_supplier_uom_factor',
        help="Factor to convert from supplier UOM to product purchase UOM"
    )

    @api.depends('supplier_uom_id', 'product_tmpl_id.uom_po_id')
    def _compute_supplier_uom_factor(self):
        """Compute the conversion factor between supplier UOM and product purchase UOM"""
        for supplier_info in self:
            factor = 1.0
            if (supplier_info.supplier_uom_id and 
                supplier_info.product_tmpl_id.uom_po_id and
                supplier_info.supplier_uom_id != supplier_info.product_tmpl_id.uom_po_id):
                
                # Check if UOMs belong to the same category
                if (supplier_info.supplier_uom_id.category_id == 
                    supplier_info.product_tmpl_id.uom_po_id.category_id):
                    
                    # Calculate conversion factor
                    factor = supplier_info.supplier_uom_id.factor / supplier_info.product_tmpl_id.uom_po_id.factor
                else:
                    factor = 1.0
            
            supplier_info.supplier_uom_factor = factor

    @api.constrains('supplier_uom_id', 'product_tmpl_id')
    def _check_supplier_uom_category(self):
        """Ensure supplier UOM belongs to the same category as product purchase UOM"""
        for supplier_info in self:
            if (supplier_info.supplier_uom_id and 
                supplier_info.product_tmpl_id.uom_po_id and
                supplier_info.supplier_uom_id.category_id != supplier_info.product_tmpl_id.uom_po_id.category_id):
                
                raise ValidationError(_(
                    'The supplier UOM "%s" must belong to the same category as '
                    'the product purchase UOM "%s".'
                ) % (supplier_info.supplier_uom_id.name, 
                     supplier_info.product_tmpl_id.uom_po_id.name))

    def _get_supplier_uom(self):
        """Get the UOM to use for this supplier (supplier UOM or product purchase UOM)"""
        self.ensure_one()
        return self.supplier_uom_id or self.product_tmpl_id.uom_po_id

    def _convert_price_to_product_uom(self, price, quantity=1.0):
        """Convert price from supplier UOM to product purchase UOM"""
        self.ensure_one()
        if not self.supplier_uom_id or self.supplier_uom_id == self.product_tmpl_id.uom_po_id:
            return price
        
        # Convert the price considering the UOM factor
        if self.supplier_uom_factor != 0:
            return price / self.supplier_uom_factor
        return price

    def _convert_quantity_to_supplier_uom(self, quantity):
        """Convert quantity from product purchase UOM to supplier UOM"""
        self.ensure_one()
        if not self.supplier_uom_id or self.supplier_uom_id == self.product_tmpl_id.uom_po_id:
            return quantity
        
        # Convert the quantity using the UOM factor
        return quantity * self.supplier_uom_factor

    @api.onchange('supplier_uom_id')
    def _onchange_supplier_uom_id(self):
        """Recalculate conversion factor when supplier UOM changes"""
        self._compute_supplier_uom_factor()

    def get_price_for_quantity(self, quantity, date=None):
        """Get price for the given quantity, handling UOM conversion"""
        self.ensure_one()
        # Get the base price from the supplier info
        price = self._get_supplier_price(quantity, date)
        
        # If we have a supplier UOM, the price should be returned as-is
        # since it's already in the supplier's UOM
        return price

    def _get_supplier_price(self, quantity, date=None):
        """Get the supplier price (override if needed for complex pricing)"""
        self.ensure_one()
        return self.price