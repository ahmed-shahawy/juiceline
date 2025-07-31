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
        string="Merchant ID",
        help="The Merchant ID provided by Geidea",
        required_if_provider='geidea'
    )
    
    geidea_terminal_id = fields.Char(
        string="Terminal ID", 
        help="The Terminal ID provided by Geidea",
        required_if_provider='geidea'
    )
    
    geidea_api_key = fields.Char(
        string="API Key",
        help="The API Key provided by Geidea",
        required_if_provider='geidea'
    )
    
    geidea_api_secret = fields.Char(
        string="API Secret",
        help="The API Secret provided by Geidea",
        required_if_provider='geidea'
    )
    
    geidea_environment = fields.Selection([
        ('test', 'Test'),
        ('production', 'Production')
    ], string="Environment", default='test', required_if_provider='geidea',
       help="Select the environment for Geidea payment processing")

    def _get_supported_currencies(self):
        """ Override to return supported currencies for Geidea. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'geidea':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['SAR', 'AED', 'USD', 'EUR']
            )
        return supported_currencies

    def _geidea_get_api_url(self):
        """ Return the appropriate API URL based on environment. """
        if self.geidea_environment == 'production':
            return 'https://api.geidea.net'
        else:
            return 'https://api-merchant.staging.geidea.net'