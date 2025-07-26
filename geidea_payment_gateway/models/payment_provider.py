# -*- coding: utf-8 -*-

import hashlib
import hmac
import json
import logging
import requests
from werkzeug.urls import url_encode

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )
    
    # Geidea-specific fields
    geidea_merchant_id = fields.Char(
        string='Merchant ID',
        required_if_provider='geidea',
        groups='base.group_user'
    )
    geidea_api_key = fields.Char(
        string='API Key',
        required_if_provider='geidea',
        groups='base.group_user'
    )
    geidea_api_password = fields.Char(
        string='API Password',
        required_if_provider='geidea',
        groups='base.group_user'
    )
    geidea_webhook_secret = fields.Char(
        string='Webhook Secret',
        groups='base.group_user',
        help='Secret key for webhook validation'
    )

    def _get_supported_currencies(self):
        """Return supported currencies for Geidea"""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'geidea':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in [
                    'AED', 'SAR', 'KWD', 'QAR', 'BHD', 'OMR', 'USD', 'EUR', 'GBP'
                ]
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """Return default payment method codes for Geidea"""
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'geidea':
            return ['card', 'wallet']
        return default_codes

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """Ensure Geidea is available for supported currencies"""
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)
        
        currency = self.env['res.currency'].browse(currency_id) if currency_id else None
        if currency and currency.name not in [
            'AED', 'SAR', 'KWD', 'QAR', 'BHD', 'OMR', 'USD', 'EUR', 'GBP'
        ]:
            providers = providers.filtered(lambda p: p.code != 'geidea')
            
        return providers

    def _geidea_get_api_url(self, endpoint=''):
        """Get Geidea API URL based on state (test/production)"""
        base_url = 'https://api-merchant.geidea.net' if self.state == 'enabled' else 'https://api-merchant-sandbox.geidea.net'
        return f"{base_url}/{endpoint}" if endpoint else base_url

    def _geidea_generate_signature(self, method, url, body=''):
        """Generate signature for Geidea API requests"""
        if not self.geidea_api_password:
            raise UserError(_("API Password is required for signature generation"))
            
        string_to_sign = f"{method.upper()}\n{url}\n{body}"
        signature = hmac.new(
            self.geidea_api_password.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _geidea_make_request(self, endpoint, data=None, method='POST'):
        """Make authenticated request to Geidea API"""
        url = self._geidea_get_api_url(endpoint)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.geidea_api_key}',
        }
        
        body = json.dumps(data) if data else ''
        signature = self._geidea_generate_signature(method, url, body)
        headers['X-Merchant-Signature'] = signature
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=60)
            else:
                response = requests.post(url, data=body, headers=headers, timeout=60)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"Geidea API request failed: {str(e)}")
            raise UserError(_("Payment processing failed. Please try again."))

    def _get_validation_amount(self):
        """Return validation amount for Geidea (minimum 1 AED)"""
        return 1.0 if self.code == 'geidea' else super()._get_validation_amount()

    def _get_validation_currency(self):
        """Return validation currency for Geidea"""
        return 'AED' if self.code == 'geidea' else super()._get_validation_currency()