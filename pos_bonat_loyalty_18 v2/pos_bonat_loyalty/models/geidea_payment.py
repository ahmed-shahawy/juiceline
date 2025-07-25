# -*- coding: utf-8 -*-
import json
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import requests
import base64
from cryptography.fernet import Fernet

_logger = logging.getLogger(__name__)


class GeideaPaymentTerminal(models.Model):
    """Model to manage Geidea payment terminals"""
    _name = 'geidea.payment.terminal'
    _description = 'Geidea Payment Terminal'
    _rec_name = 'terminal_id'

    terminal_id = fields.Char(string='Terminal ID', required=True)
    name = fields.Char(string='Terminal Name', required=True)
    pos_config_id = fields.Many2one('pos.config', string='POS Configuration')
    status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance')
    ], string='Status', default='disconnected', tracking=True)
    last_connection = fields.Datetime(string='Last Connection')
    connection_attempts = fields.Integer(string='Connection Attempts', default=0)
    error_message = fields.Text(string='Last Error Message')
    is_active = fields.Boolean(string='Active', default=True)
    last_transaction_id = fields.Char(string='Last Transaction ID')
    firmware_version = fields.Char(string='Firmware Version')
    
    # Connection settings
    ip_address = fields.Char(string='IP Address')
    port = fields.Integer(string='Port', default=8080)
    connection_timeout = fields.Integer(string='Connection Timeout (seconds)', default=30)
    
    # Performance metrics
    total_transactions = fields.Integer(string='Total Transactions', default=0)
    successful_transactions = fields.Integer(string='Successful Transactions', default=0)
    failed_transactions = fields.Integer(string='Failed Transactions', default=0)
    average_response_time = fields.Float(string='Average Response Time (ms)', default=0.0)

    @api.model
    def check_terminal_health(self, terminal_id):
        """Check the health status of a terminal"""
        terminal = self.search([('terminal_id', '=', terminal_id)], limit=1)
        if not terminal:
            return {'status': 'not_found', 'message': 'Terminal not found'}
        
        # Simulate health check - in real implementation this would ping the terminal
        try:
            # Mock health check logic
            if terminal.status == 'connected':
                return {
                    'status': 'healthy',
                    'terminal_id': terminal.terminal_id,
                    'last_connection': terminal.last_connection,
                    'response_time': terminal.average_response_time
                }
            else:
                return {
                    'status': 'unhealthy',
                    'terminal_id': terminal.terminal_id,
                    'error': terminal.error_message
                }
        except Exception as e:
            _logger.error(f"Health check failed for terminal {terminal_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}


class GeideaPaymentTransaction(models.Model):
    """Model to track Geidea payment transactions"""
    _name = 'geidea.payment.transaction'
    _description = 'Geidea Payment Transaction'
    _order = 'create_date desc'

    name = fields.Char(string='Transaction Reference', required=True, default=lambda self: self._generate_reference())
    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    pos_payment_id = fields.Many2one('pos.payment', string='POS Payment')
    terminal_id = fields.Many2one('geidea.payment.terminal', string='Terminal')
    
    # Transaction details
    transaction_id = fields.Char(string='Geidea Transaction ID')
    amount = fields.Float(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    payment_method = fields.Selection([
        ('card', 'Card Payment'),
        ('contactless', 'Contactless Payment'),
        ('mobile', 'Mobile Payment'),
        ('qr', 'QR Code Payment')
    ], string='Payment Method', required=True)
    
    # Transaction status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded')
    ], string='Status', default='draft', tracking=True)
    
    # Card details (encrypted)
    card_number_masked = fields.Char(string='Card Number (Masked)')
    card_holder_name = fields.Char(string='Card Holder Name')
    card_type = fields.Char(string='Card Type')
    
    # Timestamps
    initiated_at = fields.Datetime(string='Initiated At', default=fields.Datetime.now)
    authorized_at = fields.Datetime(string='Authorized At')
    completed_at = fields.Datetime(string='Completed At')
    
    # Error handling
    error_code = fields.Char(string='Error Code')
    error_message = fields.Text(string='Error Message')
    retry_count = fields.Integer(string='Retry Count', default=0)
    
    # Security and audit
    encrypted_data = fields.Text(string='Encrypted Transaction Data')
    checksum = fields.Char(string='Transaction Checksum')
    
    # Refund details
    original_transaction_id = fields.Many2one('geidea.payment.transaction', string='Original Transaction')
    refund_amount = fields.Float(string='Refund Amount')
    refund_reason = fields.Text(string='Refund Reason')
    
    # Performance metrics
    response_time = fields.Float(string='Response Time (ms)')
    
    @api.model
    def _generate_reference(self):
        """Generate unique transaction reference"""
        return f"GDT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    
    def _encrypt_sensitive_data(self, data):
        """Encrypt sensitive transaction data"""
        company = self.env.company
        if not company.geidea_encryption_key:
            # Generate a new encryption key if not exists
            key = Fernet.generate_key()
            company.sudo().write({'geidea_encryption_key': key.decode()})
        
        fernet = Fernet(company.geidea_encryption_key.encode())
        return fernet.encrypt(json.dumps(data).encode()).decode()
    
    def _decrypt_sensitive_data(self):
        """Decrypt sensitive transaction data"""
        if not self.encrypted_data:
            return {}
        
        company = self.env.company
        if not company.geidea_encryption_key:
            return {}
        
        try:
            fernet = Fernet(company.geidea_encryption_key.encode())
            decrypted = fernet.decrypt(self.encrypted_data.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            _logger.error(f"Failed to decrypt transaction data: {str(e)}")
            return {}
    
    def generate_checksum(self):
        """Generate transaction checksum for integrity verification"""
        data = f"{self.name}{self.amount}{self.currency_id.name}{self.payment_method}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add checksum"""
        for vals in vals_list:
            if 'checksum' not in vals:
                # Will be calculated after record creation
                pass
        
        records = super().create(vals_list)
        for record in records:
            record.checksum = record.generate_checksum()
        return records


class GeideaPaymentMethod(models.Model):
    """Extended payment method for Geidea integration"""
    _inherit = 'pos.payment.method'
    
    is_geidea_payment = fields.Boolean(string='Is Geidea Payment Method')
    geidea_payment_type = fields.Selection([
        ('card', 'Card Payment'),
        ('contactless', 'Contactless Payment'),
        ('mobile', 'Mobile Payment'),
        ('qr', 'QR Code Payment')
    ], string='Geidea Payment Type')
    terminal_id = fields.Many2one('geidea.payment.terminal', string='Default Terminal')
    enable_partial_payment = fields.Boolean(string='Enable Partial Payment', default=True)
    minimum_amount = fields.Float(string='Minimum Transaction Amount', default=0.0)
    maximum_amount = fields.Float(string='Maximum Transaction Amount', default=0.0)


class GeideaConnectionPool(models.Model):
    """Model to manage connection pool for Geidea terminals"""
    _name = 'geidea.connection.pool'
    _description = 'Geidea Connection Pool'
    
    name = fields.Char(string='Pool Name', required=True)
    max_connections = fields.Integer(string='Maximum Connections', default=5)
    active_connections = fields.Integer(string='Active Connections', default=0)
    terminal_ids = fields.Many2many('geidea.payment.terminal', string='Associated Terminals')
    last_used = fields.Datetime(string='Last Used', default=fields.Datetime.now)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('full', 'Full')
    ], string='Status', default='active')
    
    def acquire_connection(self):
        """Acquire a connection from the pool"""
        if self.active_connections < self.max_connections:
            self.active_connections += 1
            self.last_used = fields.Datetime.now()
            return True
        return False
    
    def release_connection(self):
        """Release a connection back to the pool"""
        if self.active_connections > 0:
            self.active_connections -= 1
            return True
        return False