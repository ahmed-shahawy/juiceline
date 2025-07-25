# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import logging
import platform

_logger = logging.getLogger(__name__)


class GeideaTerminal(models.Model):
    _name = 'geidea.terminal'
    _description = 'Geidea Payment Terminal'
    _order = 'name'

    name = fields.Char(string='Terminal Name', required=True)
    terminal_id = fields.Char(string='Terminal ID', required=True)
    merchant_id = fields.Char(string='Merchant ID', required=True)
    terminal_key = fields.Char(string='Terminal Key', required=True)
    
    # Connection settings
    connection_type = fields.Selection([
        ('usb', 'USB'),
        ('bluetooth', 'Bluetooth'),
        ('network', 'Network/WiFi'),
        ('serial', 'Serial Port')
    ], string='Connection Type', required=True, default='usb')
    
    # Platform detection
    platform = fields.Selection([
        ('windows', 'Windows'),
        ('ios', 'iOS/iPad'),
        ('android', 'Android'),
        ('linux', 'Linux'),
        ('auto', 'Auto-detect')
    ], string='Platform', default='auto', required=True)
    
    # Connection details
    ip_address = fields.Char(string='IP Address', help='For network connections')
    port = fields.Integer(string='Port', default=8080, help='For network connections')
    bluetooth_address = fields.Char(string='Bluetooth Address', help='For Bluetooth connections')
    serial_port = fields.Char(string='Serial Port', help='For serial connections (e.g., COM1, /dev/ttyUSB0)')
    usb_vendor_id = fields.Char(string='USB Vendor ID', help='For USB connections')
    usb_product_id = fields.Char(string='USB Product ID', help='For USB connections')
    
    # Status and monitoring
    connection_status = fields.Selection([
        ('disconnected', 'Disconnected'),
        ('connecting', 'Connecting'),
        ('connected', 'Connected'),
        ('error', 'Error')
    ], string='Connection Status', default='disconnected', readonly=True)
    
    last_connection_test = fields.Datetime(string='Last Connection Test', readonly=True)
    last_error_message = fields.Text(string='Last Error', readonly=True)
    
    # Configuration
    timeout = fields.Integer(string='Connection Timeout (seconds)', default=30)
    retry_attempts = fields.Integer(string='Retry Attempts', default=3)
    auto_reconnect = fields.Boolean(string='Auto Reconnect', default=True)
    
    # POS Configuration
    pos_config_ids = fields.Many2many('pos.config', string='POS Configurations')
    
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def get_platform_info(self):
        """Get current platform information"""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'darwin':
            return 'ios'  # Assuming iPad/iOS for macOS (will be refined in JS)
        elif system == 'linux':
            # Could be Android or Linux
            return 'android'  # Default assumption, will be refined in JS
        return 'auto'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set platform if auto"""
        for vals in vals_list:
            if vals.get('platform') == 'auto':
                vals['platform'] = self.get_platform_info()
        return super().create(vals_list)

    def test_connection(self):
        """Test terminal connection"""
        self.ensure_one()
        self.connection_status = 'connecting'
        self.last_connection_test = fields.Datetime.now()
        
        try:
            # Platform-specific connection testing will be implemented
            # This is a placeholder that will be extended with actual terminal communication
            success = self._perform_connection_test()
            
            if success:
                self.connection_status = 'connected'
                self.last_error_message = False
                return {'success': True, 'message': _('Connection successful')}
            else:
                self.connection_status = 'error'
                return {'success': False, 'message': _('Connection failed')}
                
        except Exception as e:
            self.connection_status = 'error'
            self.last_error_message = str(e)
            _logger.error(f"Terminal connection test failed: {e}")
            return {'success': False, 'message': str(e)}

    def _perform_connection_test(self):
        """Perform the actual connection test based on platform and connection type"""
        # This will be implemented with platform-specific logic
        # For now, return True as placeholder
        return True

    def disconnect(self):
        """Disconnect from terminal"""
        self.ensure_one()
        self.connection_status = 'disconnected'
        self.last_error_message = False

    def get_connection_config(self):
        """Get connection configuration for frontend"""
        self.ensure_one()
        config = {
            'terminal_id': self.terminal_id,
            'merchant_id': self.merchant_id,
            'connection_type': self.connection_type,
            'platform': self.platform,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'auto_reconnect': self.auto_reconnect,
        }
        
        # Add connection-specific details
        if self.connection_type == 'network':
            config.update({
                'ip_address': self.ip_address,
                'port': self.port,
            })
        elif self.connection_type == 'bluetooth':
            config['bluetooth_address'] = self.bluetooth_address
        elif self.connection_type == 'serial':
            config['serial_port'] = self.serial_port
        elif self.connection_type == 'usb':
            config.update({
                'usb_vendor_id': self.usb_vendor_id,
                'usb_product_id': self.usb_product_id,
            })
            
        return config

    @api.constrains('ip_address', 'connection_type')
    def _check_ip_address(self):
        """Validate IP address when using network connection"""
        for record in self:
            if record.connection_type == 'network' and record.ip_address:
                # Basic IP validation
                import ipaddress
                try:
                    ipaddress.ip_address(record.ip_address)
                except ValueError:
                    raise ValidationError(_('Invalid IP address format'))

    @api.constrains('port')
    def _check_port(self):
        """Validate port number"""
        for record in self:
            if record.port and not (1 <= record.port <= 65535):
                raise ValidationError(_('Port must be between 1 and 65535'))