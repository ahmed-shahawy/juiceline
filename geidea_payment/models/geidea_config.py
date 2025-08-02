# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class GeideaConfig(models.Model):
    _name = 'geidea.config'
    _description = 'Geidea Configuration Settings'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        help='Name of the configuration set'
    )
    
    provider_id = fields.Many2one(
        'payment.provider',
        string='Payment Provider',
        domain=[('code', '=', 'geidea')],
        required=True
    )
    
    # API Configuration
    api_version = fields.Char(
        string='API Version',
        default='v1',
        help='Geidea API version to use'
    )
    
    timeout = fields.Integer(
        string='Timeout (seconds)',
        default=30,
        help='Request timeout in seconds'
    )
    
    retry_attempts = fields.Integer(
        string='Retry Attempts',
        default=3,
        help='Number of retry attempts for failed requests'
    )
    
    # Security Settings
    enable_3ds = fields.Boolean(
        string='Enable 3D Secure',
        default=True,
        help='Enable 3D Secure authentication'
    )
    
    enable_tokenization = fields.Boolean(
        string='Enable Tokenization',
        default=False,
        help='Enable card tokenization for recurring payments'
    )
    
    # Logging and Monitoring
    enable_logging = fields.Boolean(
        string='Enable Logging',
        default=True,
        help='Enable detailed logging for transactions'
    )
    
    log_level = fields.Selection([
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string='Log Level', default='info')
    
    # Notification Settings
    enable_webhooks = fields.Boolean(
        string='Enable Webhooks',
        default=True,
        help='Enable webhook notifications from Geidea'
    )
    
    webhook_events = fields.Text(
        string='Webhook Events',
        default='payment.authorized,payment.captured,payment.failed,payment.refunded',
        help='Comma-separated list of webhook events to subscribe to'
    )
    
    # Device Management
    auto_detect_devices = fields.Boolean(
        string='Auto-detect Devices',
        default=True,
        help='Automatically detect and register new devices'
    )
    
    device_heartbeat_interval = fields.Integer(
        string='Device Heartbeat Interval (minutes)',
        default=5,
        help='Interval for device heartbeat checks'
    )
    
    # Additional Configuration
    custom_fields = fields.Text(
        string='Custom Configuration',
        help='JSON format custom configuration fields'
    )
    
    active = fields.Boolean(default=True)
    
    @api.constrains('timeout', 'retry_attempts', 'device_heartbeat_interval')
    def _check_positive_values(self):
        for config in self:
            if config.timeout <= 0:
                raise ValueError(_('Timeout must be greater than 0'))
            if config.retry_attempts < 0:
                raise ValueError(_('Retry attempts cannot be negative'))
            if config.device_heartbeat_interval <= 0:
                raise ValueError(_('Device heartbeat interval must be greater than 0'))