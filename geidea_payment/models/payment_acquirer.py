# -*- coding: utf-8 -*-
import logging
import requests
import json
import hashlib
import hmac
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('geidea', 'Geidea')], 
        ondelete={'geidea': 'set default'}
    )
    
    # Geidea specific configuration fields
    geidea_merchant_id = fields.Char(
        string='Merchant ID',
        help='Your Geidea Merchant ID',
        groups='base.group_user'
    )
    geidea_merchant_key = fields.Char(
        string='Merchant Key',
        help='Your Geidea Merchant Key',
        groups='base.group_user'
    )
    geidea_api_password = fields.Char(
        string='API Password',
        help='Your Geidea API Password',
        groups='base.group_user'
    )
    geidea_gateway_url = fields.Char(
        string='Gateway URL',
        default='https://api.merchant.geidea.net',
        help='Geidea Gateway URL (Production or Sandbox)',
        groups='base.group_user'
    )
    geidea_callback_url = fields.Char(
        string='Callback URL',
        compute='_compute_geidea_callback_url',
        help='URL where Geidea will send payment notifications',
        groups='base.group_user'
    )

    @api.depends('state')
    def _compute_geidea_callback_url(self):
        """Compute the callback URL for Geidea webhooks."""
        for acquirer in self:
            if acquirer.provider == 'geidea':
                base_url = acquirer.get_base_url()
                acquirer.geidea_callback_url = urls.url_join(
                    base_url, '/payment/geidea/webhook'
                )
            else:
                acquirer.geidea_callback_url = False

    @api.constrains('geidea_merchant_id', 'geidea_merchant_key', 'geidea_api_password')
    def _check_geidea_credentials(self):
        """Validate Geidea credentials format."""
        for acquirer in self:
            if acquirer.provider == 'geidea':
                if not acquirer.geidea_merchant_id:
                    raise ValidationError(_('Merchant ID is required for Geidea payment gateway.'))
                if not acquirer.geidea_merchant_key:
                    raise ValidationError(_('Merchant Key is required for Geidea payment gateway.'))
                if not acquirer.geidea_api_password:
                    raise ValidationError(_('API Password is required for Geidea payment gateway.'))

    def _geidea_get_api_url(self, endpoint=''):
        """Get the complete API URL for Geidea endpoints."""
        self.ensure_one()
        base_url = self.geidea_gateway_url.rstrip('/')
        if endpoint:
            return f"{base_url}/{endpoint.lstrip('/')}"
        return base_url

    def _geidea_generate_signature(self, data):
        """Generate HMAC signature for Geidea API calls."""
        self.ensure_one()
        # Sort data alphabetically and create query string
        sorted_data = sorted(data.items())
        query_string = '&'.join([f"{key}={value}" for key, value in sorted_data if value])
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.geidea_merchant_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def _geidea_make_request(self, endpoint, data, method='POST'):
        """Make authenticated request to Geidea API."""
        self.ensure_one()
        
        url = self._geidea_get_api_url(endpoint)
        
        # Add signature to data
        data['signature'] = self._geidea_generate_signature(data)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=data, headers=headers, timeout=30)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.error('Geidea API request failed: %s', str(e))
            raise UserError(_('Payment processing failed. Please try again later.'))
        except Exception as e:
            _logger.error('Unexpected error in Geidea API call: %s', str(e))
            raise UserError(_('An unexpected error occurred during payment processing.'))

    def geidea_form_generate_values(self, values):
        """Generate form values for Geidea payment form."""
        self.ensure_one()
        
        # Prepare payment data
        payment_data = {
            'merchantId': self.geidea_merchant_id,
            'amount': float_round(values['amount'], 2),
            'currency': values['currency'] and values['currency'].name or 'USD',
            'merchantReferenceId': values['reference'],
            'callbackUrl': self.geidea_callback_url,
            'returnUrl': values.get('return_url', ''),
            'language': values.get('partner_lang', 'en')[:2],
            'customerEmail': values.get('partner_email', ''),
            'customerPhone': values.get('partner_phone', ''),
            'description': values.get('reference', ''),
        }
        
        # Add billing information if available
        if values.get('billing_partner_name'):
            payment_data.update({
                'billingAddress': {
                    'name': values.get('billing_partner_name', ''),
                    'city': values.get('billing_partner_city', ''),
                    'country': values.get('billing_partner_country') and values['billing_partner_country'].code or '',
                    'street': values.get('billing_partner_address', ''),
                    'postcode': values.get('billing_partner_zip', ''),
                }
            })
        
        return payment_data

    def geidea_get_form_action_url(self):
        """Return the URL for Geidea payment form submission."""
        self.ensure_one()
        return self._geidea_get_api_url('pgw/api/v1/direct/session')

    def _get_default_payment_method_codes(self):
        """Add Geidea to default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        return default_codes + ['geidea']