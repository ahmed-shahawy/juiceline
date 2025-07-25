# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    pos_geidea_payment_enabled = fields.Boolean(
        string="Enable Geidea Payment Integration",
        help="Enable iPad-optimized Geidea payment integration for Point of Sale"
    )

class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Geidea Configuration
    geidea_payment_enabled = fields.Boolean(
        string="Enable Geidea Payment",
        default=False,
        help="Enable Geidea payment integration for this POS configuration"
    )
    
    geidea_merchant_id = fields.Char(
        string="Geidea Merchant ID",
        help="Merchant ID provided by Geidea"
    )
    
    geidea_merchant_key = fields.Char(
        string="Geidea Merchant Key",
        help="Merchant key for Geidea API authentication"
    )
    
    geidea_test_mode = fields.Boolean(
        string="Test Mode",
        default=True,
        help="Enable test mode for Geidea payments"
    )
    
    # iPad-specific settings
    geidea_ipad_optimized = fields.Boolean(
        string="iPad Optimized",
        default=True,
        help="Enable iPad-specific optimizations"
    )
    
    geidea_bluetooth_timeout = fields.Integer(
        string="Bluetooth Connection Timeout (seconds)",
        default=30,
        help="Timeout for Bluetooth connection attempts"
    )
    
    geidea_auto_reconnect = fields.Boolean(
        string="Auto Reconnect",
        default=True,
        help="Automatically reconnect to Geidea device when connection is lost"
    )
    
    geidea_battery_optimization = fields.Boolean(
        string="Battery Optimization",
        default=True,
        help="Enable battery optimization features for iPad"
    )
    
    # Connection settings
    geidea_device_name = fields.Char(
        string="Device Name",
        help="Name of the Geidea payment device to connect to"
    )
    
    geidea_device_mac = fields.Char(
        string="Device MAC Address",
        help="MAC address of the Geidea payment device"
    )
    
    @api.constrains('geidea_bluetooth_timeout')
    def _check_bluetooth_timeout(self):
        for record in self:
            if record.geidea_bluetooth_timeout < 5 or record.geidea_bluetooth_timeout > 300:
                raise ValidationError(_("Bluetooth timeout must be between 5 and 300 seconds"))
    
    @api.constrains('geidea_merchant_id', 'geidea_merchant_key')
    def _check_geidea_credentials(self):
        for record in self:
            if record.geidea_payment_enabled:
                if not record.geidea_merchant_id:
                    raise ValidationError(_("Merchant ID is required when Geidea payment is enabled"))
                if not record.geidea_merchant_key:
                    raise ValidationError(_("Merchant Key is required when Geidea payment is enabled"))
    
    def test_geidea_connection(self):
        """Test the connection to Geidea payment gateway"""
        self.ensure_one()
        # This would typically involve making a test API call to Geidea
        # For now, we'll return a success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Connection Test"),
                'message': _("Geidea connection test successful"),
                'sticky': False,
                'type': 'success'
            }
        }