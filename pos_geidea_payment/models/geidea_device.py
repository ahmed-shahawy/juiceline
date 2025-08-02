# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class GeideaDevice(models.Model):
    _name = 'geidea.device'
    _description = 'Geidea Payment Device'
    _rec_name = 'name'

    name = fields.Char(
        string='Device Name',
        required=True,
        help='Name for this payment device'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this device is active'
    )
    
    # Device Identification
    device_id = fields.Char(
        string='Device ID',
        required=True,
        help='Unique device identifier from Geidea'
    )
    
    serial_number = fields.Char(
        string='Serial Number',
        help='Device serial number'
    )
    
    model = fields.Char(
        string='Device Model',
        help='Device model name'
    )
    
    # Platform Information
    platform = fields.Selection([
        ('windows', 'Windows'),
        ('android', 'Android'),
        ('ios', 'iOS/iPad'),
        ('web', 'Web Browser'),
        ('other', 'Other')
    ], string='Platform', required=True, default='windows',
       help='Device platform')
    
    platform_version = fields.Char(
        string='Platform Version',
        help='Operating system version'
    )
    
    # Configuration
    config_id = fields.Many2one(
        'geidea.config',
        string='Geidea Configuration',
        required=True,
        ondelete='cascade',
        help='Associated Geidea configuration'
    )
    
    pos_config_id = fields.Many2one(
        'pos.config',
        string='POS Configuration',
        help='Associated POS configuration'
    )
    
    # Network Configuration
    ip_address = fields.Char(
        string='IP Address',
        help='Device IP address'
    )
    
    port = fields.Integer(
        string='Port',
        default=8080,
        help='Communication port'
    )
    
    mac_address = fields.Char(
        string='MAC Address',
        help='Device MAC address'
    )
    
    # Connection Settings
    connection_type = fields.Selection([
        ('tcp', 'TCP/IP'),
        ('usb', 'USB'),
        ('bluetooth', 'Bluetooth'),
        ('wifi', 'WiFi'),
        ('http', 'HTTP/HTTPS')
    ], string='Connection Type', default='tcp',
       help='Type of connection to the device')
    
    # Status and Monitoring
    status = fields.Selection([
        ('offline', 'Offline'),
        ('online', 'Online'),
        ('busy', 'Busy'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance')
    ], string='Status', default='offline',
       help='Current device status')
    
    last_seen = fields.Datetime(
        string='Last Seen',
        help='Last time device was online'
    )
    
    last_transaction_date = fields.Datetime(
        string='Last Transaction',
        help='Date of last transaction processed'
    )
    
    # Device Capabilities
    supports_contactless = fields.Boolean(
        string='Supports Contactless',
        default=True,
        help='Device supports contactless payments'
    )
    
    supports_chip_pin = fields.Boolean(
        string='Supports Chip & PIN',
        default=True,
        help='Device supports chip and PIN payments'
    )
    
    supports_magstripe = fields.Boolean(
        string='Supports Magnetic Stripe',
        default=True,
        help='Device supports magnetic stripe cards'
    )
    
    supports_mobile_payment = fields.Boolean(
        string='Supports Mobile Payment',
        default=True,
        help='Device supports mobile payment methods'
    )
    
    # Transaction Statistics
    transaction_ids = fields.One2many(
        'geidea.transaction',
        'device_id',
        string='Transactions',
        help='Transactions processed by this device'
    )
    
    total_transactions = fields.Integer(
        string='Total Transactions',
        compute='_compute_transaction_stats',
        help='Total transactions processed by this device'
    )
    
    successful_transactions = fields.Integer(
        string='Successful Transactions',
        compute='_compute_transaction_stats',
        help='Successful transactions processed by this device'
    )
    
    failed_transactions = fields.Integer(
        string='Failed Transactions',
        compute='_compute_transaction_stats',
        help='Failed transactions processed by this device'
    )
    
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_transaction_stats',
        currency_field='currency_id',
        help='Total amount processed by this device'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='config_id.currency_id',
        string='Currency'
    )
    
    # Device Settings
    receipt_settings = fields.Text(
        string='Receipt Settings',
        help='Device-specific receipt settings in JSON format'
    )
    
    display_settings = fields.Text(
        string='Display Settings',
        help='Device-specific display settings in JSON format'
    )
    
    # Error Handling
    error_message = fields.Text(
        string='Last Error',
        help='Last error message from device'
    )
    
    error_count = fields.Integer(
        string='Error Count',
        default=0,
        help='Number of consecutive errors'
    )

    @api.depends('transaction_ids')
    def _compute_transaction_stats(self):
        """Compute transaction statistics for each device"""
        for device in self:
            transactions = device.transaction_ids
            
            device.total_transactions = len(transactions)
            
            successful = transactions.filtered(lambda t: t.state == 'completed')
            device.successful_transactions = len(successful)
            device.total_amount = sum(successful.mapped('amount'))
            
            device.failed_transactions = len(transactions.filtered(
                lambda t: t.state == 'failed'
            ))

    @api.constrains('device_id')
    def _check_device_id_unique(self):
        """Ensure device ID is unique within configuration"""
        for device in self:
            if self.search_count([
                ('device_id', '=', device.device_id),
                ('config_id', '=', device.config_id.id),
                ('id', '!=', device.id)
            ]) > 0:
                raise ValidationError(_(
                    'Device ID must be unique within the same configuration'
                ))

    @api.constrains('ip_address')
    def _check_ip_address(self):
        """Validate IP address format"""
        import re
        for device in self:
            if device.ip_address:
                ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
                if not re.match(ip_pattern, device.ip_address):
                    raise ValidationError(_('Invalid IP address format'))

    def test_connection(self):
        """Test connection to device"""
        self.ensure_one()
        try:
            # Implementation for testing device connection
            self.status = 'online'
            self.last_seen = fields.Datetime.now()
            self.error_count = 0
            self.error_message = False
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Device Connection'),
                    'message': _('Successfully connected to device %s') % self.name,
                    'type': 'success',
                }
            }
        except Exception as e:
            self.status = 'error'
            self.error_message = str(e)
            self.error_count += 1
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Device Connection Error'),
                    'message': _('Failed to connect to device %s: %s') % (self.name, str(e)),
                    'type': 'danger',
                }
            }

    def reset_device(self):
        """Reset device to initial state"""
        self.ensure_one()
        try:
            # Implementation for resetting device
            self.status = 'offline'
            self.error_count = 0
            self.error_message = False
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Device Reset'),
                    'message': _('Device %s has been reset') % self.name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Device Reset Error'),
                    'message': _('Failed to reset device %s: %s') % (self.name, str(e)),
                    'type': 'danger',
                }
            }

    def update_status(self, status, error_message=None):
        """Update device status"""
        self.ensure_one()
        self.status = status
        self.last_seen = fields.Datetime.now()
        
        if error_message:
            self.error_message = error_message
            self.error_count += 1
        else:
            self.error_count = 0
            self.error_message = False

    @api.model
    def cron_check_device_status(self):
        """Cron job to check device status"""
        devices = self.search([('active', '=', True)])
        for device in devices:
            try:
                # Implementation for checking device status
                # This would ping the device or check last activity
                pass
            except Exception as e:
                device.update_status('error', str(e))
                _logger.error('Device %s status check failed: %s', device.name, str(e))