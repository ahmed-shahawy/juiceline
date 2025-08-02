# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    # Geidea Integration
    use_geidea_payment = fields.Boolean(
        string='Use Geidea Payment',
        default=False,
        help='Use Geidea payment processing for this payment method'
    )
    
    geidea_config_id = fields.Many2one(
        'geidea.config',
        string='Geidea Configuration',
        help='Geidea configuration to use for this payment method'
    )
    
    geidea_payment_type = fields.Selection([
        ('card', 'Credit/Debit Card'),
        ('contactless', 'Contactless'),
        ('mobile', 'Mobile Payment'),
        ('wallet', 'Digital Wallet')
    ], string='Geidea Payment Type',
       help='Type of Geidea payment method')

    @api.onchange('use_geidea_payment')
    def _onchange_use_geidea_payment(self):
        """Set payment terminal type when Geidea is enabled"""
        if self.use_geidea_payment:
            self.use_payment_terminal = 'geidea'
        else:
            self.geidea_config_id = False
            self.geidea_payment_type = False