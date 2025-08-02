# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Geidea Integration Settings
    enable_geidea_integration = fields.Boolean(
        string='Enable Geidea Integration',
        default=False,
        help='Enable Geidea payment integration for this company'
    )
    
    geidea_api_key = fields.Char(
        string='Geidea API Key',
        help='API key for Geidea payment service'
    )
    
    geidea_merchant_id = fields.Char(
        string='Geidea Merchant ID',
        help='Merchant identifier in Geidea system'
    )
    
    geidea_terminal_id = fields.Char(
        string='Geidea Terminal ID',
        help='Terminal identifier for payment device'
    )
    
    geidea_environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], string='Geidea Environment', default='sandbox',
       help='Geidea environment to use')
    
    geidea_auto_capture = fields.Boolean(
        string='Auto Capture Payments',
        default=True,
        help='Automatically capture payments after authorization'
    )
    
    geidea_timeout = fields.Integer(
        string='Transaction Timeout',
        default=30,
        help='Timeout for payment transactions in seconds'
    )