# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    supplier_uom_id = fields.Many2one(
        'uom.uom',
        string='Supplier UoM',
        compute='_compute_supplier_uom',
        store=True,
        help="Unit of measure used by the supplier for this product"
    )
    supplier_uom_factor = fields.Float(
        string='Supplier UoM Factor',
        compute='_compute_supplier_uom',
        store=True,
        help="Factor used to convert supplier UoM to product UoM"
    )

    @api.depends('product_id', 'partner_id')
    def _compute_supplier_uom(self):
        for line in self:
            supplier_info = line._find_supplier_info()
            if supplier_info and supplier_info.supplier_uom_id:
                line.supplier_uom_id = supplier_info.supplier_uom_id.id
                line.supplier_uom_factor = supplier_info.supplier_uom_factor
            else:
                line.supplier_uom_id = line.product_uom.id if line.product_uom else False
                line.supplier_uom_factor = 1.0

    def _find_supplier_info(self):
        """Find the supplier info record for the current product and partner."""
        self.ensure_one()
        if not self.product_id or not self.partner_id:
            return False

        domain = [
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('name', '=', self.partner_id.id),
        ]
        # Check for product variant specific supplier info
        if self.product_id.product_tmpl_id.product_variant_count > 1:
            domain = [
                '|',
                '&', ('product_id', '=', self.product_id.id), ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                '&', ('product_id', '=', False), ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ] + domain[1:]

        return self.env['product.supplierinfo'].search(domain, limit=1)

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        
        # Update price based on supplier UoM if needed
        supplier_info = self._find_supplier_info()
        if supplier_info and supplier_info.supplier_uom_id and supplier_info.supplier_uom_id != self.product_uom:
            # Convert price from supplier UoM to purchase UoM
            self.price_unit = supplier_info._get_price_in_supplier_uom(
                self.price_unit, self.product_uom
            )
            
        return res
