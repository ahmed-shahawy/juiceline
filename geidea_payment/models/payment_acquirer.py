# -*- coding: utf-8 -*-

import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('geidea', 'Geidea')],
        ondelete={'geidea': 'set default'}
    )
    
    geidea_merchant_id = fields.Char(
        string="Merchant ID",
        help="Your Geidea merchant identifier",
        required_if_provider='geidea'
    )
    
    geidea_api_key = fields.Char(
        string="API Key",
        help="Your Geidea API key for authentication",
        required_if_provider='geidea'
    )
    
    geidea_test_mode = fields.Boolean(
        string="Test Mode",
        default=True,
        help="Enable test mode for Geidea payments"
    )

    def _get_default_payment_method_codes(self):
        """ Override to add Geidea payment methods. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'geidea':
            return default_codes
        return ['card']  # Geidea supports card payments

    def _geidea_make_request(self, endpoint, data=None, method='POST'):
        """ Make a request to Geidea API """
        base_url = 'https://api-sandbox.geidea.net' if self.geidea_test_mode else 'https://api.geidea.net'
        url = f"{base_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.geidea_api_key}',
            'Content-Type': 'application/json',
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Geidea API request failed: {str(e)}")
            raise UserError(_("Payment processing failed. Please try again."))


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    geidea_merchant_id = fields.Char(string="Geidea Merchant ID")
    geidea_api_key = fields.Char(string="Geidea API Key")
    geidea_test_mode = fields.Boolean(string="Geidea Test Mode", default=True)