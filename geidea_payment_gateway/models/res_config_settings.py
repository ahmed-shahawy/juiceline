# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # POS configuration reference
    pos_config_id = fields.Many2one(
        comodel_name='pos.config',
        string='POS Configuration',
        help='Reference to the POS configuration settings'
    )
    # Epson printer configuration
    pos_epson_printer_ip = fields.Char(
        related='pos_config_id.pos_epson_printer_ip',
        readonly=False,
        string='Epson Printer IP Address',
        help='IP address of the Epson printer for POS receipt printing'
    )
    
    # Geidea payment gateway settings
    geidea_merchant_id = fields.Char(
        related='pos_config_id.geidea_merchant_id',
        readonly=False,
        string='Geidea Merchant ID',
        help='Merchant ID provided by Geidea'
    )
    geidea_api_key = fields.Char(
        related='pos_config_id.geidea_api_key',
        readonly=False,
        string='Geidea API Key',
        help='API Key for Geidea payment processing'
    )
    geidea_api_password = fields.Char(
        related='pos_config_id.geidea_api_password',
        readonly=False,
        string='Geidea API Password',
        help='API Password for Geidea payment processing'
    )
    geidea_test_mode = fields.Boolean(
        related='pos_config_id.geidea_test_mode',
        readonly=False,
        string='Geidea Test Mode',
        help='Enable test mode for Geidea payments'
    )