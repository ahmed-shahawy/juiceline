# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    use_payment_terminal = fields.Selection(
        selection_add=[('geidea', 'Geidea Terminal')],
        ondelete={'geidea': 'set default'}
    )
    
    geidea_terminal_id = fields.Many2one(
        'geidea.terminal',
        string='Geidea Terminal',
        help='Geidea terminal to use for this payment method'
    )

    @api.onchange('use_payment_terminal')
    def _onchange_use_payment_terminal(self):
        """Clear Geidea terminal when not using Geidea"""
        if self.use_payment_terminal != 'geidea':
            self.geidea_terminal_id = False

    def _get_payment_terminal_selection(self):
        """Override to include Geidea option"""
        return super()._get_payment_terminal_selection() + [('geidea', 'Geidea Terminal')]