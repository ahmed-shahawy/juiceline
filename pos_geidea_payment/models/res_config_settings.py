# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Geidea Integration Settings
    enable_geidea_integration = fields.Boolean(
        string='Enable Geidea Payment Integration',
        related='company_id.enable_geidea_integration',
        readonly=False,
        help='Enable Geidea payment integration for this company'
    )
    
    geidea_api_key = fields.Char(
        string='Geidea API Key',
        related='company_id.geidea_api_key',
        readonly=False,
        help='API key for Geidea payment service'
    )
    
    geidea_merchant_id = fields.Char(
        string='Geidea Merchant ID',
        related='company_id.geidea_merchant_id',
        readonly=False,
        help='Merchant identifier in Geidea system'
    )
    
    geidea_terminal_id = fields.Char(
        string='Geidea Terminal ID',
        related='company_id.geidea_terminal_id',
        readonly=False,
        help='Terminal identifier for payment device'
    )
    
    geidea_environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], string='Geidea Environment',
       related='company_id.geidea_environment',
       readonly=False,
       help='Geidea environment to use')
    
    geidea_auto_capture = fields.Boolean(
        string='Auto Capture Payments',
        related='company_id.geidea_auto_capture',
        readonly=False,
        help='Automatically capture payments after authorization'
    )
    
    geidea_timeout = fields.Integer(
        string='Transaction Timeout (seconds)',
        related='company_id.geidea_timeout',
        readonly=False,
        help='Timeout for payment transactions in seconds'
    )

    @api.onchange('enable_geidea_integration')
    def _onchange_enable_geidea_integration(self):
        """Clear sensitive data if integration is disabled"""
        if not self.enable_geidea_integration:
            self.geidea_api_key = False
            self.geidea_merchant_id = False
            self.geidea_terminal_id = False

    def action_create_geidea_config(self):
        """Create a Geidea configuration from company settings"""
        if not self.enable_geidea_integration:
            return
        
        config_vals = {
            'name': '%s - Geidea Config' % self.company_id.name,
            'api_key': self.geidea_api_key,
            'merchant_id': self.geidea_merchant_id,
            'terminal_id': self.geidea_terminal_id,
            'environment': self.geidea_environment or 'sandbox',
            'auto_capture': self.geidea_auto_capture,
            'timeout': self.geidea_timeout or 30,
            'company_id': self.company_id.id,
        }
        
        config = self.env['geidea.config'].create(config_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Geidea Configuration',
            'res_model': 'geidea.config',
            'res_id': config.id,
            'view_mode': 'form',
            'target': 'current',
        }