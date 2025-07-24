from odoo import fields, models, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_geidea = fields.Boolean('Enable Geidea Payments', default=False)
    geidea_terminal_ids = fields.Many2many(
        'geidea.terminal',
        string='Geidea Terminals',
        help='Terminals that can be used with this POS'
    )

    @api.onchange('enable_geidea')
    def _onchange_enable_geidea(self):
        if self.enable_geidea:
            payment_method = self.env['pos.payment.method'].create({
                'name': 'Geidea',
                'use_payment_terminal': 'geidea',
                'split_transactions': False,
            })
            if payment_method not in self.payment_method_ids:
                self.payment_method_ids = [(4, payment_method.id)]
        else:
            payment_methods = self.payment_method_ids.filtered(
                lambda pm: pm.use_payment_terminal == 'geidea'
            )
            if payment_methods:
                self.payment_method_ids = [(3, pm.id) for pm in payment_methods]