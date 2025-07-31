# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """Payment provider model for Geidea integration."""
    
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )
    
    # Geidea-specific configuration fields
    # Note: tracking=False to prevent sensitive data logging in audit trails (Security fix #1)
    geidea_merchant_id = fields.Char(
        string='Merchant ID',
        help='Geidea Merchant ID provided by Geidea',
        groups='base.group_system',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_public_key = fields.Char(
        string='Public Key',
        help='Geidea Public Key for API authentication',
        groups='base.group_system',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_private_key = fields.Char(
        string='Private Key',
        help='Geidea Private Key for API authentication',
        groups='base.group_system',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_gateway_url = fields.Char(
        string='Gateway URL',
        default='https://api.merchant.geidea.net',
        help='Geidea Gateway URL for API calls',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_test_mode = fields.Boolean(
        string='Test Mode',
        default=True,
        help='Enable test mode for Geidea transactions',
    )
    geidea_currency_code = fields.Char(
        string='Currency Code',
        default='SAR',
        help='Default currency code for Geidea transactions',
    )
    geidea_timeout = fields.Integer(
        string='API Timeout (seconds)',
        default=30,
        help='Timeout for Geidea API calls in seconds',
    )

    @api.constrains('geidea_merchant_id', 'geidea_public_key', 'geidea_private_key')
    def _check_geidea_credentials(self):
        """Validate Geidea credentials when provider is enabled."""
        for provider in self:
            if provider.code == 'geidea' and provider.state != 'disabled':
                if not provider.geidea_merchant_id:
                    raise ValidationError(_('Merchant ID is required for Geidea provider.'))
                if not provider.geidea_public_key:
                    raise ValidationError(_('Public Key is required for Geidea provider.'))
                if not provider.geidea_private_key:
                    raise ValidationError(_('Private Key is required for Geidea provider.'))

    def _get_supported_currencies(self):
        """Return supported currencies for Geidea."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'geidea':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['SAR', 'USD', 'EUR', 'AED', 'KWD', 'BHD', 'OMR', 'QAR']
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """Return default payment method codes for Geidea."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'geidea':
            return ['card']
        return default_codes

    @api.model
    def _get_geidea_urls(self, environment):
        """Get Geidea API URLs based on environment."""
        if environment == 'prod':
            return {
                'geidea_form_url': 'https://api.merchant.geidea.net/pgw/api/v1/direct/pay',
                'geidea_rest_url': 'https://api.merchant.geidea.net/pgw/api/v1',
            }
        else:
            return {
                'geidea_form_url': 'https://api-merchant.staging.geidea.net/pgw/api/v1/direct/pay',
                'geidea_rest_url': 'https://api-merchant.staging.geidea.net/pgw/api/v1',
            }

    def _geidea_get_api_url(self, endpoint=''):
        """
        Get the full API URL for Geidea endpoints.
        
        Args:
            endpoint (str): The API endpoint to append to base URL
            
        Returns:
            str: Complete API URL
        """
        base_url = self.geidea_gateway_url.rstrip('/')
        if self.geidea_test_mode:
            base_url = 'https://api-merchant.staging.geidea.net'
        
        if endpoint:
            return f"{base_url}/pgw/api/v1/{endpoint.lstrip('/')}"
        return f"{base_url}/pgw/api/v1"

    def _geidea_make_request(self, endpoint, data=None, method='POST'):
        """
        Make asynchronous request to Geidea API with proper error handling.
        This method will be implemented in the transaction model to handle async calls.
        """
        # This method signature is defined here but implementation
        # will be in the payment.transaction model to handle async processing
        pass