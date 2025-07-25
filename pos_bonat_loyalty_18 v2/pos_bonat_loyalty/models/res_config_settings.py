from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_bonat_integration = fields.Boolean(related='company_id.enable_bonat_integration', readonly=False)
    bonat_api_key = fields.Char(related='company_id.bonat_api_key', readonly=False)
    bonat_merchant_name = fields.Char(related='company_id.bonat_merchant_name', readonly=False)
    bonat_merchant_id = fields.Char(related='company_id.bonat_merchant_id', readonly=False)
    
    # Geidea Payment Integration Settings
    enable_geidea_integration = fields.Boolean(related='company_id.enable_geidea_integration', readonly=False)
    geidea_api_key = fields.Char(related='company_id.geidea_api_key', readonly=False)
    geidea_api_password = fields.Char(related='company_id.geidea_api_password', readonly=False)
    geidea_merchant_id = fields.Char(related='company_id.geidea_merchant_id', readonly=False)
    geidea_terminal_id = fields.Char(related='company_id.geidea_terminal_id', readonly=False)
    geidea_environment = fields.Selection(related='company_id.geidea_environment', readonly=False)
    geidea_connection_timeout = fields.Integer(related='company_id.geidea_connection_timeout', readonly=False)
    geidea_enable_partial_payments = fields.Boolean(related='company_id.geidea_enable_partial_payments', readonly=False)
    geidea_enable_refunds = fields.Boolean(related='company_id.geidea_enable_refunds', readonly=False)
    geidea_encryption_key = fields.Char(related='company_id.geidea_encryption_key', readonly=False)
    geidea_max_retry_attempts = fields.Integer(related='company_id.geidea_max_retry_attempts', readonly=False)
    geidea_connection_pool_size = fields.Integer(related='company_id.geidea_connection_pool_size', readonly=False)
    # bonat_discount_percentage_product_id = fields.Many2one(related='company_id.bonat_discount_percentage_product_id', readonly=False)

    @api.onchange('enable_bonat_integration')
    def _onchange_enable_bonat_integration(self):
        """Clear API key if integration is disabled."""
        if not self.enable_bonat_integration:
            self.bonat_api_key = False
            
    @api.onchange('enable_geidea_integration')
    def _onchange_enable_geidea_integration(self):
        """Clear Geidea settings if integration is disabled."""
        if not self.enable_geidea_integration:
            self.geidea_api_key = False
            self.geidea_api_password = False
            self.geidea_merchant_id = False
            self.geidea_terminal_id = False
            self.geidea_encryption_key = False
