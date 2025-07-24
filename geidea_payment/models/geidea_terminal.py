from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
import json
import requests
from datetime import datetime
from cryptography.fernet import Fernet

_logger = logging.getLogger(__name__)

class GeideaTerminal(models.Model):
    _name = 'geidea.terminal'
    _description = 'Geidea Payment Terminal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Terminal Name', required=True, tracking=True)
    terminal_id = fields.Char('Terminal ID', required=True, tracking=True)
    merchant_id = fields.Char('Merchant ID', required=True, tracking=True)
    api_key = fields.Char('API Key', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error')
    ], default='draft', tracking=True)
    
    pos_config_ids = fields.Many2many('pos.config', string='POS Points')
    last_sync = fields.Datetime('Last Synchronization')
    transaction_count = fields.Integer(compute='_compute_transaction_count')
    success_rate = fields.Float(compute='_compute_success_rate')
    
    encryption_key = fields.Char('Encryption Key', copy=False)
    
    @api.model
    def create(self, vals):
        # Generate encryption key for secure storage
        if not vals.get('encryption_key'):
            vals['encryption_key'] = Fernet.generate_key().decode()
        return super().create(vals)
    
    def _encrypt_sensitive_data(self, data):
        f = Fernet(self.encryption_key.encode())
        return f.encrypt(data.encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data):
        f = Fernet(self.encryption_key.encode())
        return f.decrypt(encrypted_data.encode()).decode()
    
    @api.constrains('terminal_id')
    def _check_terminal_id(self):
        for terminal in self:
            if self.search_count([
                ('terminal_id', '=', terminal.terminal_id),
                ('id', '!=', terminal.id)
            ]):
                raise ValidationError(_('Terminal ID must be unique!'))
    
    def action_activate(self):
        self.ensure_one()
        try:
            # Test connection to Geidea API
            self._test_connection()
            self.state = 'active'
            self.message_post(body=_("Terminal activated successfully"))
        except Exception as e:
            self.state = 'error'
            self.message_post(body=_("Activation failed: %s") % str(e))
    
    def _test_connection(self):
        headers = {
            'Authorization': f"Bearer {self._decrypt_sensitive_data(self.api_key)}",
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{self._get_api_url()}/terminal/status",
            headers=headers,
            params={'terminalId': self.terminal_id}
        )
        
        if response.status_code != 200:
            raise ValidationError(_("Connection test failed: %s") % response.text)
    
    def _get_api_url(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        return ICPSudo.get_param('geidea.api_url', 'https://api.geidea.net/v1')
    
    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for terminal in self:
            terminal.transaction_count = self.env['geidea.transaction'].search_count([
                ('terminal_id', '=', terminal.id)
            ])
    
    @api.depends('transaction_ids.state')
    def _compute_success_rate(self):
        for terminal in self:
            transactions = self.env['geidea.transaction'].search([
                ('terminal_id', '=', terminal.id)
            ])
            total = len(transactions)
            if total:
                successful = len(transactions.filtered(lambda t: t.state == 'completed'))
                terminal.success_rate = (successful / total) * 100
            else:
                terminal.success_rate = 0