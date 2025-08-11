from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    purchase_uom_id = fields.Many2one(
        "uom.uom",
        string="Vendor Purchase UoM",
        help="Unit used by this vendor when purchasing this product.",
    )

    @api.constrains("purchase_uom_id", "product_tmpl_id")
    def _check_purchase_uom_category(self):
        for rec in self:
            if rec.purchase_uom_id and rec.product_tmpl_id and rec.product_tmpl_id.uom_id:
                if rec.purchase_uom_id.category_id != rec.product_tmpl_id.uom_id.category_id:
                    raise ValidationError(
                        _("Vendor Purchase UoM must be in the same category as the product's base UoM."))