# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Properly define currency_provider as related field without selection attribute
    # The selection options come from the related field in res.company
    currency_provider = fields.Selection(
        related='company_id.currency_provider',
        readonly=False
    )
    
    # Geidea specific configuration fields
    geidea_merchant_id = fields.Char(
        string="Geidea Merchant ID",
        related='company_id.geidea_merchant_id',
        readonly=False,
        help="Your Geidea merchant identifier"
    )
    
    geidea_api_key = fields.Char(
        string="Geidea API Key",
        related='company_id.geidea_api_key',
        readonly=False,
        help="Your Geidea API key for authentication"
    )
    
    geidea_test_mode = fields.Boolean(
        string="Test Mode",
        related='company_id.geidea_test_mode',
        readonly=False,
        help="Enable test mode for Geidea payments"
    )