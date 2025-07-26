# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class GeideaDevice(models.Model):
    _name = 'geidea.device'
    _description = 'Geidea Payment Device'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Device Name',
        required=True,
        help="Name identifier for the payment device"
    )
    
    device_id = fields.Char(
        string='Device ID',
        required=True,
        help="Unique device identifier from Geidea"
    )
    
    serial_number = fields.Char(
        string='Serial Number',
        help="Physical device serial number"
    )
    
    device_type = fields.Selection([
        ('windows', 'Windows Terminal'),
        ('ipad', 'iPad POS'),
        ('android', 'Android Tablet')
    ], string='Device Type', required=True)
    
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error')
    ], string='Connection Status', default='disconnected')
    
    last_connected = fields.Datetime(
        string='Last Connected',
        help="Last time device was successfully connected"
    )
    
    acquirer_id = fields.Many2one(
        'payment.acquirer.geidea',
        string='Payment Acquirer',
        required=True
    )
    
    pos_config_id = fields.Many2one(
        'pos.config',
        string='POS Configuration'
    )
    
    active = fields.Boolean(string='Active', default=True)
    
    firmware_version = fields.Char(
        string='Firmware Version',
        help="Current firmware version of the device"
    )
    
    ip_address = fields.Char(
        string='IP Address',
        help="IP address for network-connected devices"
    )
    
    port = fields.Integer(
        string='Port',
        help="Communication port for network devices"
    )

    def connect_device(self):
        """Connect to the payment device"""
        self.ensure_one()
        try:
            # Placeholder for actual device connection logic
            self.connection_status = 'connected'
            self.last_connected = fields.Datetime.now()
            _logger.info(f"Connected to device: {self.name}")
            return True
        except Exception as e:
            self.connection_status = 'error'
            _logger.error(f"Failed to connect to device {self.name}: {str(e)}")
            return False

    def disconnect_device(self):
        """Disconnect from the payment device"""
        self.ensure_one()
        self.connection_status = 'disconnected'
        _logger.info(f"Disconnected from device: {self.name}")

    def test_device(self):
        """Test device functionality"""
        self.ensure_one()
        if self.connect_device():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Device test successful!"),
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Device test failed!"),
                    'type': 'danger',
                }
            }