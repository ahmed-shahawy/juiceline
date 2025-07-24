from odoo import fields, models, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_geidea = fields.Boolean('Enable Geidea Payments', default=False)
    geidea_api_key = fields.Char('Geidea API Key')
    geidea_merchant_id = fields.Char('Geidea Merchant ID')
    geidea_terminal_id = fields.Char('Geidea Terminal ID')
    geidea_test_mode = fields.Boolean('Test Mode', default=True)
    
    @api.onchange('enable_geidea')
    def _onchange_enable_geidea(self):
        if self.enable_geidea:
            geidea_payment_method = self.env['pos.payment.method'].search([
                ('use_payment_terminal', '=', 'geidea')
            ], limit=1)
            if not geidea_payment_method:
                geidea_payment_method = self.env['pos.payment.method'].create({
                    'name': 'Geidea',
                    'use_payment_terminal': 'geidea',
                    'split_transactions': False,
                })
            if geidea_payment_method not in self.payment_method_ids:
                self.payment_method_ids = [(4, geidea_payment_method.id)]