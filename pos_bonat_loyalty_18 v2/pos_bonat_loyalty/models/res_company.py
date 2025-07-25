# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_bonat_integration = fields.Boolean(string="Enable Bonat Integration")
    bonat_api_key = fields.Char(string="Bonat API Key")
    bonat_merchant_name = fields.Char(string="Merchant Name", default="Name")
    bonat_merchant_id = fields.Char(string="Merchant ID", default="ABCD1234")
    
    # Geidea Payment Integration Settings
    enable_geidea_integration = fields.Boolean(string="Enable Geidea Payment Integration")
    geidea_api_key = fields.Char(string="Geidea API Key")
    geidea_api_password = fields.Char(string="Geidea API Password")
    geidea_merchant_id = fields.Char(string="Geidea Merchant ID")
    geidea_terminal_id = fields.Char(string="Geidea Terminal ID")
    geidea_environment = fields.Selection([
        ('test', 'Test Environment'),
        ('production', 'Production Environment')
    ], string="Geidea Environment", default='test')
    geidea_connection_timeout = fields.Integer(string="Connection Timeout (seconds)", default=30)
    geidea_enable_partial_payments = fields.Boolean(string="Enable Partial Payments", default=True)
    geidea_enable_refunds = fields.Boolean(string="Enable Refunds", default=True)
    geidea_encryption_key = fields.Char(string="Encryption Key for Sensitive Data")
    geidea_max_retry_attempts = fields.Integer(string="Max Retry Attempts", default=3)
    geidea_connection_pool_size = fields.Integer(string="Connection Pool Size", default=5)

    @api.model
    def _load_pos_data_fields(self, config_id):
        return super()._load_pos_data_fields(config_id) + [
            "enable_bonat_integration", "bonat_api_key", "bonat_merchant_id", "bonat_merchant_name",
            "enable_geidea_integration", "geidea_api_key", "geidea_merchant_id", "geidea_terminal_id",
            "geidea_environment", "geidea_connection_timeout", "geidea_enable_partial_payments",
            "geidea_enable_refunds", "geidea_max_retry_attempts", "geidea_connection_pool_size"
        ]

    @api.model
    def get_bonat_code_response(self, code):
        """
        Validate the Bonat code via Bonat API and include allowed_products in the response.
        """

        company = self.env.company
        if not company.enable_bonat_integration or not company.bonat_api_key:
            return {"success": False, "error": _("Bonat integration is not enabled or API key is missing.")}

        api_url = "https://api.bonat.io/odoo_partner/reward-check"
        # api_url = "https://stg-api.bonat.io/odoo_partner/reward-check"
        headers = {
            "Authorization": f"Bearer {company.bonat_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "reward_code": code,
            "merchant_id": company.bonat_merchant_id
        }

        try:
            # Make API Request
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            # import pdb;pdb.set_trace()
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data"):
                    api_data = data.get("data")
                    # Add allowed_products to the API response data
                    # api_data["allowed_products"] = allowed_products
                    return {"success": True, "data": api_data}
                else:
                    return {"success": False, "error": data.get("errors", "This code has already been used. Please try a different one.")}
            else:
                return {"success": False, "error": _("API Error: %s") % response.text}
        except requests.exceptions.RequestException as e:
            _logger.error(f"Bonat API Request Exception: {str(e)}")
            return {"success": False}
