# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )