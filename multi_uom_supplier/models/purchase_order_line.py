# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    supplier_uom = fields.Many2one(
        'uom.uom',
        string='Supplier UOM',
        help="Unit of measure used by the supplier for this product"
    )

    @api.depends('product_id', 'partner_id')
    def _compute_supplier_uom(self):
        """Compute supplier UOM based on product and supplier"""
        for line in self:
            line.supplier_uom = False
            if line.product_id and line.partner_id:
                # Find supplier info for this product and partner
                supplier_info = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.partner_id
                )
                if supplier_info:
                    # Use the first matching supplier info
                    supplier_info = supplier_info[0]
                    line.supplier_uom = supplier_info._get_supplier_uom()

    supplier_uom = fields.Many2one(compute='_compute_supplier_uom', store=True)

    @api.onchange('product_id', 'partner_id')
    def _onchange_product_supplier_uom(self):
        """Update UOM when product or supplier changes"""
        if self.product_id and self.partner_id:
            # Get supplier info
            supplier_info = self.product_id.seller_ids.filtered(
                lambda s: s.partner_id == self.partner_id
            )
            if supplier_info:
                supplier_info = supplier_info[0]
                supplier_uom = supplier_info._get_supplier_uom()
                if supplier_uom and supplier_uom != self.product_uom:
                    # Convert quantity from product UOM to supplier UOM
                    if self.product_qty and self.product_uom:
                        converted_qty = self.product_uom._compute_quantity(
                            self.product_qty, supplier_uom
                        )
                        self.product_qty = converted_qty
                    self.product_uom = supplier_uom

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        """Override to handle supplier UOM conversion"""
        res = super()._onchange_quantity()
        
        # Update supplier UOM when UOM changes
        if self.product_uom:
            self.supplier_uom = self.product_uom
            
        return res

    def _prepare_account_move_line(self, move=False):
        """Override to ensure proper UOM conversion for accounting"""
        res = super()._prepare_account_move_line(move)
        
        # Ensure quantity is converted to product's base UOM for accounting
        if self.supplier_uom and self.product_id.uom_id != self.supplier_uom:
            # Convert from supplier UOM to product base UOM
            converted_qty = self.supplier_uom._compute_quantity(
                self.product_qty, self.product_id.uom_id
            )
            res['quantity'] = converted_qty
            
        return res

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, 
                                                     product_uom, company_id, supplier, 
                                                     po):
        """Override to handle supplier UOM in procurement"""
        res = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, supplier, po
        )
        
        # Find supplier info and set appropriate UOM
        if supplier and product_id:
            product = self.env['product.product'].browse(product_id)
            supplier_info = product.seller_ids.filtered(
                lambda s: s.partner_id.id == supplier.id
            )
            if supplier_info:
                supplier_info = supplier_info[0]
                supplier_uom = supplier_info._get_supplier_uom()
                if supplier_uom:
                    # Convert quantity to supplier UOM
                    if product_uom != supplier_uom:
                        converted_qty = self.env['uom.uom'].browse(product_uom)._compute_quantity(
                            product_qty, supplier_uom
                        )
                        res.update({
                            'product_qty': converted_qty,
                            'product_uom': supplier_uom.id,
                        })
        
        return res