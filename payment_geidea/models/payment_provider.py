# -*- coding: utf-8 -*-

import logging
import requests
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')], ondelete={'geidea': 'set default'}
    )
    
    # Geidea specific configuration fields
    geidea_merchant_id = fields.Char(
        string="Merchant ID",
        help="The Merchant ID provided by Geidea",
        groups='base.group_system'
    )
    geidea_api_key = fields.Char(
        string="API Key",
        help="The API Key provided by Geidea",
        groups='base.group_system'
    )
    geidea_merchant_password = fields.Char(
        string="Merchant Password",
        help="The Merchant Password provided by Geidea",
        groups='base.group_system'
    )
    geidea_api_url = fields.Char(
        string="API URL",
        default="https://api.geidea.net",
        help="Geidea API URL (use https://api-test.geidea.net for testing)",
        groups='base.group_system'
    )
    
    # Custom Geidea features
    geidea_enable_tokenization = fields.Boolean(
        string="Enable Tokenization",
        default=False,
        help="Allow customers to save their payment methods for future use"
    )
    geidea_enable_express_checkout = fields.Boolean(
        string="Enable Express Checkout",
        default=False,
        help="Allow faster checkout for returning customers"
    )
    geidea_pos_integration = fields.Boolean(
        string="POS Integration",
        default=False,
        help="Enable Geidea payment processing in Point of Sale"
    )

    @api.constrains('geidea_merchant_id', 'geidea_api_key', 'geidea_merchant_password')
    def _check_geidea_credentials(self):
        """Validate that all required Geidea credentials are provided."""
        for provider in self:
            if provider.code == 'geidea':
                if not all([provider.geidea_merchant_id, provider.geidea_api_key, provider.geidea_merchant_password]):
                    raise ValidationError(_(
                        "All Geidea credentials (Merchant ID, API Key, and Merchant Password) are required."
                    ))

    def _geidea_get_api_url(self):
        """Get the appropriate Geidea API URL based on environment."""
        self.ensure_one()
        if self.state == 'test':
            return "https://api-test.geidea.net"
        return self.geidea_api_url or "https://api.geidea.net"

    def _geidea_make_request(self, endpoint, data=None, method='POST'):
        """Make a request to the Geidea API."""
        self.ensure_one()
        
        url = urls.url_join(self._geidea_get_api_url(), endpoint)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.geidea_api_key}',
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error("Geidea API request failed: %s", e)
            raise ValidationError(_("Communication with Geidea failed. Please check your configuration."))

    def _get_supported_currencies(self):
        """Override to specify supported currencies for Geidea."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'geidea':
            # Geidea typically supports major currencies, adjust based on actual support
            supported_currencies = ['EGP', 'USD', 'EUR', 'AED', 'SAR', 'KWD', 'QAR', 'BHD']
        return supported_currencies

    def _get_supported_countries(self):
        """Override to specify supported countries for Geidea."""
        supported_countries = super()._get_supported_countries()
        if self.code == 'geidea':
            # Geidea operates primarily in the Middle East and Africa
            supported_countries = ['EG', 'AE', 'SA', 'KW', 'QA', 'BH', 'JO', 'LB']
        return supported_countries