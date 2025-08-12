# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        """Override to use supplier-specific UOM when creating purchase order lines"""
        values = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, supplier, po
        )
        
        # Find supplier info for this product and supplier
        supplier_info = self.env['product.supplierinfo'].search([
            ('partner_id', '=', supplier.id),
            ('product_tmpl_id', '=', product_id.product_tmpl_id.id),
        ], limit=1)
        
        if supplier_info and supplier_info.supplier_uom_id:
            # Convert quantity to supplier UOM
            supplier_qty = supplier_info._convert_quantity_to_supplier_uom(product_qty)
            values.update({
                'product_qty': supplier_qty,
                'product_uom': supplier_info.supplier_uom_id.id,
            })
        
        return values


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    supplier_uom_id = fields.Many2one(
        'uom.uom',
        string='Supplier UOM',
        compute='_compute_supplier_uom_id',
        help="Unit of measure used by the supplier for this product"
    )

    @api.depends('partner_id', 'product_id')
    def _compute_supplier_uom_id(self):
        """Compute the supplier UOM based on supplier info"""
        for line in self:
            supplier_uom = False
            if line.partner_id and line.product_id:
                supplier_info = self.env['product.supplierinfo'].search([
                    ('partner_id', '=', line.partner_id.id),
                    ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ], limit=1)
                if supplier_info:
                    supplier_uom = supplier_info._get_supplier_uom()
            line.supplier_uom_id = supplier_uom

    @api.onchange('product_id', 'partner_id')
    def _onchange_product_id_supplier_uom(self):
        """Update UOM when product or supplier changes"""
        if self.product_id and self.partner_id:
            supplier_info = self.env['product.supplierinfo'].search([
                ('partner_id', '=', self.partner_id.id),
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ], limit=1)
            
            if supplier_info and supplier_info.supplier_uom_id:
                # Use supplier UOM and convert quantity if needed
                if self.product_uom != supplier_info.supplier_uom_id:
                    # Convert current quantity to supplier UOM
                    if self.product_qty and self.product_uom:
                        new_qty = self.product_uom._compute_quantity(
                            self.product_qty,
                            supplier_info.supplier_uom_id
                        )
                        self.product_qty = new_qty
                    self.product_uom = supplier_info.supplier_uom_id

    def _prepare_account_move_line(self, move=False):
        """Override to ensure proper UOM conversion for accounting"""
        vals = super()._prepare_account_move_line(move)
        
        # If we have a supplier UOM different from product UOM, 
        # ensure proper quantity conversion for inventory valuation
        if (self.supplier_uom_id and 
            self.supplier_uom_id != self.product_id.uom_po_id):
            
            # Convert quantity to product UOM for accounting purposes
            product_qty = self.product_uom._compute_quantity(
                self.product_qty,
                self.product_id.uom_po_id
            )
            vals['quantity'] = product_qty
        
        return vals