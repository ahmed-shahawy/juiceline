# -*- coding: utf-8 -*-
import logging
import requests
import json
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class GeideaPaymentAcquirer(models.Model):
    _name = 'geidea.payment.acquirer'
    _description = 'Geidea Payment Acquirer Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    
    # Geidea Configuration
    merchant_id = fields.Char('Merchant ID', required=True, tracking=True)
    terminal_id = fields.Char('Terminal ID', required=True, tracking=True)
    api_key = fields.Char('API Key', required=True, tracking=True)
    api_secret = fields.Char('API Secret', required=True, tracking=True)
    
    # Environment Configuration
    environment = fields.Selection([
        ('test', 'Test Environment'),
        ('production', 'Production Environment')
    ], string='Environment', default='test', required=True, tracking=True)
    
    # API URLs
    test_api_url = fields.Char('Test API URL', default='https://api-staging.geidea.net', tracking=True)
    production_api_url = fields.Char('Production API URL', default='https://api.geidea.net', tracking=True)
    
    # POS Configuration
    pos_config_ids = fields.Many2many('pos.config', string='POS Configurations')
    
    # Transaction Settings
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    timeout = fields.Integer('Timeout (seconds)', default=30, help="Payment request timeout in seconds")
    
    # Status and logs
    last_connection_test = fields.Datetime('Last Connection Test')
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error')
    ], string='Connection Status', default='disconnected')
    
    @api.model
    def get_api_url(self):
        """Get the appropriate API URL based on environment"""
        return self.production_api_url if self.environment == 'production' else self.test_api_url
    
    def test_connection(self):
        """Test connection to Geidea API"""
        self.ensure_one()
        try:
            url = f"{self.get_api_url()}/api/v1/health"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                self.connection_status = 'connected'
                self.last_connection_test = fields.Datetime.now()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Connection to Geidea API successful!'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                self.connection_status = 'error'
                raise UserError(_('Failed to connect to Geidea API. Status: %s') % response.status_code)
                
        except Exception as e:
            self.connection_status = 'error'
            _logger.error(f"Geidea connection test failed: {str(e)}")
            raise UserError(_('Connection test failed: %s') % str(e))


class GeideaPaymentTransaction(models.Model):
    _name = 'geidea.payment.transaction'
    _description = 'Geidea Payment Transaction'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Transaction Reference', required=True, tracking=True)
    acquirer_id = fields.Many2one('geidea.payment.acquirer', string='Geidea Acquirer', required=True)
    
    # Transaction Details
    amount = fields.Monetary('Amount', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    
    # Geidea Transaction Data
    geidea_transaction_id = fields.Char('Geidea Transaction ID', tracking=True)
    geidea_order_id = fields.Char('Geidea Order ID', tracking=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error'),
        ('refunded', 'Refunded')
    ], string='Status', default='draft', tracking=True)
    
    # POS Integration
    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    pos_session_id = fields.Many2one('pos.session', string='POS Session')
    
    # Response Data
    response_data = fields.Text('Response Data')
    error_message = fields.Text('Error Message')
    
    # Timestamps
    transaction_date = fields.Datetime('Transaction Date', default=fields.Datetime.now)
    authorized_date = fields.Datetime('Authorized Date')
    captured_date = fields.Datetime('Captured Date')
    
    def _prepare_payment_request(self):
        """Prepare payment request data for Geidea API"""
        self.ensure_one()
        return {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'merchantReferenceId': self.name,
            'callbackUrl': f"{self.env['ir.config_parameter'].get_param('web.base.url')}/geidea/payment/callback",
            'returnUrl': f"{self.env['ir.config_parameter'].get_param('web.base.url')}/geidea/payment/return",
            'merchantId': self.acquirer_id.merchant_id,
            'terminalId': self.acquirer_id.terminal_id,
        }
    
    def send_payment_request(self):
        """Send payment request to Geidea API"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_('Only draft transactions can be sent for payment.'))
        
        try:
            url = f"{self.acquirer_id.get_api_url()}/api/v1/payments"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.acquirer_id.api_key}'
            }
            
            data = self._prepare_payment_request()
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data, 
                timeout=self.acquirer_id.timeout
            )
            
            response_json = response.json()
            self.response_data = json.dumps(response_json, indent=2)
            
            if response.status_code == 200 and response_json.get('success'):
                self.geidea_transaction_id = response_json.get('transactionId')
                self.geidea_order_id = response_json.get('orderId')
                self.state = 'pending'
                _logger.info(f"Payment request sent successfully for transaction {self.name}")
                return response_json
            else:
                self.state = 'error'
                self.error_message = response_json.get('message', 'Unknown error')
                raise UserError(_('Payment request failed: %s') % self.error_message)
                
        except Exception as e:
            self.state = 'error'
            self.error_message = str(e)
            _logger.error(f"Payment request failed for transaction {self.name}: {str(e)}")
            raise UserError(_('Payment request failed: %s') % str(e))
    
    def capture_payment(self):
        """Capture authorized payment"""
        self.ensure_one()
        
        if self.state != 'authorized':
            raise UserError(_('Only authorized transactions can be captured.'))
        
        try:
            url = f"{self.acquirer_id.get_api_url()}/api/v1/payments/{self.geidea_transaction_id}/capture"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.acquirer_id.api_key}'
            }
            
            data = {
                'amount': self.amount,
                'currency': self.currency_id.name
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data, 
                timeout=self.acquirer_id.timeout
            )
            
            response_json = response.json()
            
            if response.status_code == 200 and response_json.get('success'):
                self.state = 'captured'
                self.captured_date = fields.Datetime.now()
                _logger.info(f"Payment captured successfully for transaction {self.name}")
                return True
            else:
                self.error_message = response_json.get('message', 'Capture failed')
                raise UserError(_('Payment capture failed: %s') % self.error_message)
                
        except Exception as e:
            self.error_message = str(e)
            _logger.error(f"Payment capture failed for transaction {self.name}: {str(e)}")
            raise UserError(_('Payment capture failed: %s') % str(e))
    
    def cancel_payment(self):
        """Cancel payment transaction"""
        self.ensure_one()
        
        if self.state not in ['pending', 'authorized']:
            raise UserError(_('Only pending or authorized transactions can be cancelled.'))
        
        try:
            url = f"{self.acquirer_id.get_api_url()}/api/v1/payments/{self.geidea_transaction_id}/cancel"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.acquirer_id.api_key}'
            }
            
            response = requests.post(url, headers=headers, timeout=self.acquirer_id.timeout)
            response_json = response.json()
            
            if response.status_code == 200 and response_json.get('success'):
                self.state = 'cancelled'
                _logger.info(f"Payment cancelled successfully for transaction {self.name}")
                return True
            else:
                self.error_message = response_json.get('message', 'Cancellation failed')
                raise UserError(_('Payment cancellation failed: %s') % self.error_message)
                
        except Exception as e:
            self.error_message = str(e)
            _logger.error(f"Payment cancellation failed for transaction {self.name}: {str(e)}")
            raise UserError(_('Payment cancellation failed: %s') % str(e))


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    geidea_acquirer_id = fields.Many2one(
        'geidea.payment.acquirer', 
        string='Geidea Payment Acquirer',
        help='Geidea payment acquirer for this POS configuration'
    )
    
    geidea_enabled = fields.Boolean(
        'Enable Geidea Payments', 
        default=False,
        help='Enable Geidea payment integration for this POS'
    )


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def _loader_params_geidea_payment_acquirer(self):
        """Load Geidea acquirer parameters for POS session"""
        return {
            'search_params': {
                'domain': [('active', '=', True), ('pos_config_ids', 'in', self.config_id.id)],
                'fields': ['name', 'merchant_id', 'terminal_id', 'environment', 'currency_id'],
            },
        }
    
    def _get_pos_ui_geidea_payment_acquirer(self, params):
        """Get Geidea acquirer data for POS UI"""
        return self.env['geidea.payment.acquirer'].search_read(**params['search_params'])
    
    def _loader_params_pos_payment_method(self):
        """Extend payment method loader to include Geidea"""
        result = super()._loader_params_pos_payment_method()
        if self.config_id.geidea_enabled and self.config_id.geidea_acquirer_id:
            result['search_params']['domain'].append(['geidea_enabled', '=', True])
        return result