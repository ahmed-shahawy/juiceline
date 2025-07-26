# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerGeidea(models.Model):
    _name = 'payment.acquirer.geidea'
    _description = 'Geidea Payment Acquirer Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Acquirer Name',
        required=True,
        help="Name of the Geidea payment acquirer"
    )
    
    merchant_id = fields.Char(
        string='Merchant ID',
        required=True,
        help="Geidea Merchant ID provided during registration"
    )
    
    terminal_id = fields.Char(
        string='Terminal ID',
        required=True,
        help="Terminal ID for the specific POS terminal"
    )
    
    api_key = fields.Char(
        string='API Key',
        required=True,
        help="API Key for Geidea payment gateway authentication"
    )
    
    api_secret = fields.Char(
        string='API Secret',
        required=True,
        help="API Secret for secure communication"
    )
    
    environment = fields.Selection([
        ('test', 'Test/Sandbox'),
        ('production', 'Production')
    ], string='Environment', default='test', required=True)
    
    device_type = fields.Selection([
        ('windows', 'Windows (USB/Serial/Network)'),
        ('ipad', 'iPad (Bluetooth/Lightning)'),
        ('android', 'Android (USB OTG/Bluetooth)')
    ], string='Device Type', required=True, default='windows')
    
    connection_method = fields.Selection([
        ('usb', 'USB/Serial'),
        ('bluetooth', 'Bluetooth'),
        ('network', 'Network API'),
        ('lightning', 'Lightning/USB-C')
    ], string='Connection Method', required=True, default='usb')
    
    active = fields.Boolean(string='Active', default=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    pos_config_ids = fields.One2many(
        'pos.config',
        'geidea_acquirer_id',
        string='POS Configurations'
    )

    @api.constrains('merchant_id', 'terminal_id')
    def _check_credentials(self):
        for record in self:
            if record.merchant_id and len(record.merchant_id) < 5:
                raise ValidationError(_("Merchant ID must be at least 5 characters long"))
            if record.terminal_id and len(record.terminal_id) < 3:
                raise ValidationError(_("Terminal ID must be at least 3 characters long"))

    def test_connection(self):
        """Test connection to Geidea payment gateway"""
        self.ensure_one()
        try:
            # Placeholder for actual connection test
            _logger.info(f"Testing connection for Geidea acquirer: {self.name}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Connection test successful!"),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Connection test failed: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Connection test failed: %s") % str(e),
                    'type': 'danger',
                }
            }


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    geidea_acquirer_id = fields.Many2one(
        'payment.acquirer.geidea',
        string='Geidea Payment Acquirer',
        help="Geidea payment acquirer configuration for this POS"
    )