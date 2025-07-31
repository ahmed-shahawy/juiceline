# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )
    
    geidea_merchant_key = fields.Char(
        string='Merchant Key',
        help='Your Geidea merchant key',
        groups='base.group_system'
    )
    
    geidea_merchant_password = fields.Char(
        string='Merchant Password', 
        help='Your Geidea merchant password',
        groups='base.group_system'
    )
    
    geidea_merchant_public_key = fields.Char(
        string='Merchant Public Key',
        help='Your Geidea merchant public key for client-side encryption',
        groups='base.group_system'
    )

    def _geidea_get_supported_currencies(self):
        """Return the currencies supported by Geidea."""
        return ['AED', 'USD', 'EUR', 'SAR', 'EGP']

    def _get_supported_currencies(self):
        """Override to add Geidea supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'geidea':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in self._geidea_get_supported_currencies()
            )
        return supported_currencies