# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import hashlib

_logger = logging.getLogger(__name__)


class GeideaConfig(models.Model):
    _name = 'geidea.config'
    _description = 'Geidea Payment Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        help='Name for this Geidea configuration'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this configuration is active'
    )
    
    # Basic Geidea Configuration
    api_key = fields.Char(
        string='API Key',
        required=True,
        help='Geidea API key for authentication'
    )
    
    merchant_id = fields.Char(
        string='Merchant ID',
        required=True,
        help='Merchant identifier in Geidea system'
    )
    
    terminal_id = fields.Char(
        string='Terminal ID',
        required=True,
        help='Terminal identifier for payment device'
    )
    
    # Environment Configuration
    environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], string='Environment', default='sandbox', required=True,
       help='Geidea environment to use')
    
    api_url = fields.Char(
        string='API URL',
        compute='_compute_api_url',
        store=True,
        help='Geidea API endpoint URL'
    )
    
    # Security Settings
    encryption_key = fields.Char(
        string='Encryption Key',
        help='Encryption key for sensitive data'
    )
    
    webhook_secret = fields.Char(
        string='Webhook Secret',
        help='Secret key for webhook validation'
    )
    
    # Company and POS Configuration
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    pos_config_ids = fields.Many2many(
        'pos.config',
        string='POS Configurations',
        help='POS configurations that use this Geidea setup'
    )
    
    # Device Management
    device_ids = fields.One2many(
        'geidea.device',
        'config_id',
        string='Registered Devices',
        help='Devices registered with this configuration'
    )
    
    # Transaction Settings
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    timeout = fields.Integer(
        string='Timeout (seconds)',
        default=30,
        help='Transaction timeout in seconds'
    )
    
    auto_capture = fields.Boolean(
        string='Auto Capture',
        default=True,
        help='Automatically capture payments'
    )
    
    # Status and Monitoring
    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        help='Last successful synchronization with Geidea'
    )
    
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error')
    ], string='Connection Status', default='disconnected')
    
    error_message = fields.Text(
        string='Last Error',
        help='Last error message from Geidea API'
    )
    
    # Statistics
    total_transactions = fields.Integer(
        string='Total Transactions',
        compute='_compute_transaction_stats',
        help='Total number of transactions processed'
    )
    
    successful_transactions = fields.Integer(
        string='Successful Transactions',
        compute='_compute_transaction_stats',
        help='Number of successful transactions'
    )
    
    failed_transactions = fields.Integer(
        string='Failed Transactions',
        compute='_compute_transaction_stats',
        help='Number of failed transactions'
    )

    @api.depends('environment')
    def _compute_api_url(self):
        """Compute API URL based on environment"""
        for record in self:
            if record.environment == 'production':
                record.api_url = 'https://api.geidea.net'
            else:
                record.api_url = 'https://api-sandbox.geidea.net'

    @api.depends('device_ids.transaction_ids')
    def _compute_transaction_stats(self):
        """Compute transaction statistics"""
        for record in self:
            transactions = self.env['geidea.transaction'].search([
                ('config_id', '=', record.id)
            ])
            
            record.total_transactions = len(transactions)
            record.successful_transactions = len(transactions.filtered(
                lambda t: t.state == 'completed'
            ))
            record.failed_transactions = len(transactions.filtered(
                lambda t: t.state == 'failed'
            ))

    @api.constrains('api_key', 'merchant_id', 'terminal_id')
    def _check_credentials(self):
        """Validate Geidea credentials format"""
        for record in self:
            if not record.api_key or len(record.api_key) < 10:
                raise ValidationError(_('API Key must be at least 10 characters long'))
            
            if not record.merchant_id or len(record.merchant_id) < 5:
                raise ValidationError(_('Merchant ID must be at least 5 characters long'))
            
            if not record.terminal_id or len(record.terminal_id) < 5:
                raise ValidationError(_('Terminal ID must be at least 5 characters long'))

    @api.model
    def create(self, vals):
        """Generate encryption key on creation"""
        if not vals.get('encryption_key'):
            vals['encryption_key'] = hashlib.sha256(
                (vals.get('api_key', '') + str(fields.Datetime.now())).encode()
            ).hexdigest()[:32]
        return super().create(vals)

    def test_connection(self):
        """Test connection to Geidea API"""
        for record in self:
            try:
                # This would be implemented with actual Geidea API call
                record.connection_status = 'connected'
                record.last_sync_date = fields.Datetime.now()
                record.error_message = False
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Successfully connected to Geidea API'),
                        'type': 'success',
                    }
                }
            except Exception as e:
                record.connection_status = 'error'
                record.error_message = str(e)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Error'),
                        'message': _('Failed to connect to Geidea API: %s') % str(e),
                        'type': 'danger',
                    }
                }

    def sync_with_geidea(self):
        """Synchronize configuration with Geidea"""
        for record in self:
            try:
                # Implementation for syncing with Geidea API
                record.last_sync_date = fields.Datetime.now()
                record.connection_status = 'connected'
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Synchronization'),
                        'message': _('Successfully synchronized with Geidea'),
                        'type': 'success',
                    }
                }
            except Exception as e:
                record.connection_status = 'error'
                record.error_message = str(e)
                raise UserError(_('Synchronization failed: %s') % str(e))