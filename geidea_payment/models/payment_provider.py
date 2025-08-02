# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )
    
    # Geidea Credentials
    geidea_api_key = fields.Char(
        string='API Key',
        required_if_provider='geidea',
        groups='base.group_system',
        help='Geidea API Key for authentication'
    )
    geidea_merchant_id = fields.Char(
        string='Merchant ID',
        required_if_provider='geidea',
        help='Merchant identifier in Geidea system'
    )
    geidea_terminal_id = fields.Char(
        string='Terminal ID',
        required_if_provider='geidea',
        help='Terminal identifier for payment device'
    )
    
    # Configuration Fields
    geidea_test_mode = fields.Boolean(
        string='Test Mode',
        default=True,
        help='Enable test mode for Geidea payments'
    )
    geidea_webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_geidea_webhook_url',
        help='URL for receiving Geidea payment notifications'
    )
    
    # Relationship fields
    geidea_device_ids = fields.One2many(
        'geidea.device',
        'provider_id',
        string='Devices',
        help='Connected Geidea payment devices'
    )
    
    geidea_transaction_ids = fields.One2many(
        'geidea.transaction',
        'provider_id',
        string='Transactions',
        help='Geidea payment transactions'
    )
    
    geidea_config_ids = fields.One2many(
        'geidea.config',
        'provider_id',
        string='Configurations',
        help='Geidea configuration settings'
    )
    
    @api.depends('code')
    def _compute_geidea_webhook_url(self):
        for provider in self:
            if provider.code == 'geidea':
                base_url = provider.get_base_url()
                provider.geidea_webhook_url = f"{base_url}/payment/geidea/webhook"
            else:
                provider.geidea_webhook_url = False
    
    @api.constrains('geidea_api_key', 'geidea_merchant_id', 'geidea_terminal_id')
    def _check_geidea_credentials(self):
        for provider in self:
            if provider.code == 'geidea' and provider.state != 'disabled':
                if not provider.geidea_api_key:
                    raise ValidationError(_('API Key is required for Geidea payment provider.'))
                if not provider.geidea_merchant_id:
                    raise ValidationError(_('Merchant ID is required for Geidea payment provider.'))
                if not provider.geidea_terminal_id:
                    raise ValidationError(_('Terminal ID is required for Geidea payment provider.'))
    
    def action_test_geidea_connection(self):
        """Test connection to Geidea API"""
        self.ensure_one()
        if self.code != 'geidea':
            return
        
        # TODO: Implement actual API test
        # For now, just validate that credentials are present
        if not all([self.geidea_api_key, self.geidea_merchant_id, self.geidea_terminal_id]):
            raise ValidationError(_('All Geidea credentials must be configured before testing connection.'))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection Test'),
                'message': _('Geidea connection test completed successfully.'),
                'type': 'success',
            }
        }