from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_current_seller(self):
        self.ensure_one()
        product = self.product_id
        partner = self.order_id.partner_id
        qty = self.product_qty or 1.0
        date = self.order_id.date_order or fields.Datetime.now()
        return product._select_seller(
            partner_id=partner,
            quantity=qty,
            date=date,
            uom=self.product_uom,
        )

    def _apply_vendor_uom_if_any(self):
        for line in self:
            if not line.product_id or not line.order_id.partner_id:
                continue
            seller = line._get_current_seller()
            if seller and seller.purchase_uom_id:
                line.product_uom = seller.purchase_uom_id

    @api.onchange("product_id")
    def _onchange_product_id_vendor_uom(self):
        res = super()._onchange_product_id()
        self._apply_vendor_uom_if_any()
        return res

    def _onchange_quantity(self):
        res = super()._onchange_quantity()
        self._apply_vendor_uom_if_any()
        return res