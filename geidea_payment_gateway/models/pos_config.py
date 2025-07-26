# -*- coding: utf-8 -*-

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Fix for missing pos_epson_printer_ip field
    pos_epson_printer_ip = fields.Char(
        string='Epson Printer IP',
        help='IP address of the Epson printer for receipt printing in POS'
    )
    
    # Geidea Payment Gateway fields
    geidea_merchant_id = fields.Char(
        string='Geidea Merchant ID',
        help='Merchant ID provided by Geidea'
    )
    geidea_api_key = fields.Char(
        string='Geidea API Key',
        help='API Key for Geidea payment processing'
    )
    geidea_api_password = fields.Char(
        string='Geidea API Password',
        help='API Password for Geidea payment processing'
    )
    geidea_test_mode = fields.Boolean(
        string='Test Mode',
        default=True,
        help='Enable test mode for Geidea payments'
    )
    
    def _load_pos_data_fields(self):
        """Add Geidea and printer fields to POS data"""
        fields = super()._load_pos_data_fields()
        fields.extend([
            'pos_epson_printer_ip',
            'geidea_merchant_id',
            'geidea_api_key',
            'geidea_api_password',
            'geidea_test_mode'
        ])
        return fields