# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_uom_ids = fields.One2many(
        'supplier.uom',
        'partner_id',
        string='وحدات قياس المورد'
    )
    supplier_uom_count = fields.Integer(
        string='عدد وحدات القياس',
        compute='_compute_supplier_uom_count'
    )

    @api.depends('supplier_uom_ids')
    def _compute_supplier_uom_count(self):
        for partner in self:
            partner.supplier_uom_count = len(partner.supplier_uom_ids)

    def action_view_supplier_uoms(self):
        """عرض وحدات قياس المورد"""
        self.ensure_one()
        action = self.env.ref('supplier_unit_measurement.action_supplier_uom').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action