from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_bonat_integration = fields.Boolean(related='company_id.enable_bonat_integration', readonly=False)
    bonat_api_key = fields.Char(related='company_id.bonat_api_key', readonly=False)
    bonat_merchant_name = fields.Char(related='company_id.bonat_merchant_name', readonly=False)
    bonat_merchant_id = fields.Char(related='company_id.bonat_merchant_id', readonly=False)
    bonat_cache_timeout = fields.Integer(related='company_id.bonat_cache_timeout', readonly=False)
    bonat_retry_attempts = fields.Integer(related='company_id.bonat_retry_attempts', readonly=False)

    @api.onchange('enable_bonat_integration')
    def _onchange_enable_bonat_integration(self):
        """Handle changes to Bonat integration setting."""
        if not self.enable_bonat_integration:
            # Clear sensitive data when disabling integration
            self.bonat_api_key = False
        else:
            # Set default values when enabling integration
            if not self.bonat_cache_timeout:
                self.bonat_cache_timeout = 5
            if not self.bonat_retry_attempts:
                self.bonat_retry_attempts = 3
    
    @api.onchange('bonat_cache_timeout')
    def _onchange_bonat_cache_timeout(self):
        """Validate cache timeout range."""
        if self.bonat_cache_timeout and (self.bonat_cache_timeout < 1 or self.bonat_cache_timeout > 60):
            raise ValidationError("Cache timeout must be between 1 and 60 minutes.")
    
    @api.onchange('bonat_retry_attempts')
    def _onchange_bonat_retry_attempts(self):
        """Validate retry attempts range."""
        if self.bonat_retry_attempts and (self.bonat_retry_attempts < 1 or self.bonat_retry_attempts > 10):
            raise ValidationError("Retry attempts must be between 1 and 10.")
    
    def test_bonat_connection(self):
        """Test connection to Bonat API."""
        if not self.enable_bonat_integration:
            raise ValidationError("Please enable Bonat integration first.")
        
        if not self.bonat_api_key:
            raise ValidationError("Please enter your Bonat API key.")
        
        # Test with a simple API call
        company = self.env.company
        test_response = company.get_bonat_code_response("TEST_CONNECTION_CODE")
        
        if test_response.get("success"):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Connection Successful",
                    'message': "Successfully connected to Bonat API.",
                    'type': 'success',
                }
            }
        else:
            error_msg = test_response.get("error", ["Connection failed"])[0]
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Connection Failed",
                    'message': f"Failed to connect to Bonat API: {error_msg}",
                    'type': 'danger',
                }
            }
