# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )

    # Geidea specific fields
    geidea_merchant_id = fields.Char(
        string='Merchant ID',
        help='The Merchant ID provided by Geidea',
        required_if_provider='geidea'
    )
    geidea_api_key = fields.Char(
        string='API Key',
        help='The API Key provided by Geidea',
        required_if_provider='geidea'
    )
    geidea_merchant_password = fields.Char(
        string='Merchant Password',
        help='The Merchant Password provided by Geidea',
        required_if_provider='geidea'
    )

    def _get_supported_currencies(self):
        """Override to specify supported currencies for Geidea."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'geidea':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['SAR', 'AED', 'KWD', 'BHD', 'QAR', 'OMR', 'USD', 'EUR']
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """Override to specify default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'geidea':
            return ['card']
        return default_codes