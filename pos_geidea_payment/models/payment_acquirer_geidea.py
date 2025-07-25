from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
import requests
from cryptography.fernet import Fernet

_logger = logging.getLogger(__name__)

class PaymentAcquirerGeidea(models.Model):
    _name = 'payment.acquirer.geidea'
    _description = 'Geidea Payment Acquirer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Acquirer Name', required=True, tracking=True)
    
    # API Configuration
    merchant_id = fields.Char('Merchant ID', required=True, tracking=True)
    api_key = fields.Char('API Key', required=True, tracking=True)
    api_password = fields.Char('API Password', required=True, tracking=True)
    
    # Environment Settings
    environment = fields.Selection([
        ('test', 'Test Environment'),
        ('production', 'Production Environment')
    ], required=True, default='test', tracking=True)
    
    api_url_test = fields.Char(
        'Test API URL', 
        default='https://api-test.geidea.net/v1',
        required=True
    )
    api_url_production = fields.Char(
        'Production API URL', 
        default='https://api.geidea.net/v1',
        required=True
    )
    
    # Status and Configuration
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error')
    ], default='draft', tracking=True)
    
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        default=lambda self: self.env.company,
        required=True
    )
    
    # Multi-currency support
    currency_ids = fields.Many2many(
        'res.currency',
        string='Supported Currencies',
        help='Currencies supported by this Geidea acquirer'
    )
    
    # Security Settings
    encryption_key = fields.Char('Encryption Key', copy=False)
    webhook_secret = fields.Char('Webhook Secret Key', tracking=True)
    
    # Transaction Settings
    auto_capture = fields.Boolean('Auto Capture', default=True)
    capture_manually = fields.Boolean('Manual Capture', default=False)
    
    # Fees and Limits
    fixed_fee = fields.Float('Fixed Fee', digits='Product Price')
    percentage_fee = fields.Float('Percentage Fee (%)', digits=(16, 2))
    minimum_amount = fields.Float('Minimum Amount', digits='Product Price')
    maximum_amount = fields.Float('Maximum Amount', digits='Product Price')
    
    # Terminal Configuration
    terminal_ids = fields.One2many(
        'geidea.terminal',
        'acquirer_id',
        string='Terminals'
    )
    
    # Statistics
    transaction_count = fields.Integer(
        compute='_compute_transaction_stats',
        string='Total Transactions'
    )
    success_rate = fields.Float(
        compute='_compute_transaction_stats',
        string='Success Rate (%)'
    )
    total_amount = fields.Float(
        compute='_compute_transaction_stats',
        string='Total Amount',
        digits='Product Price'
    )
    
    @api.model
    def create(self, vals):
        if not vals.get('encryption_key'):
            vals['encryption_key'] = Fernet.generate_key().decode()
        return super().create(vals)
    
    def _encrypt_sensitive_data(self, data):
        """Encrypt sensitive data using Fernet encryption"""
        if not data:
            return data
        f = Fernet(self.encryption_key.encode())
        return f.encrypt(data.encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data using Fernet encryption"""
        if not encrypted_data:
            return encrypted_data
        f = Fernet(self.encryption_key.encode())
        return f.decrypt(encrypted_data.encode()).decode()
    
    @api.depends('terminal_ids.transaction_ids')
    def _compute_transaction_stats(self):
        for acquirer in self:
            transactions = acquirer.terminal_ids.mapped('transaction_ids')
            acquirer.transaction_count = len(transactions)
            
            if transactions:
                successful = transactions.filtered(lambda t: t.state == 'completed')
                acquirer.success_rate = (len(successful) / len(transactions)) * 100
                acquirer.total_amount = sum(t.amount for t in successful)
            else:
                acquirer.success_rate = 0.0
                acquirer.total_amount = 0.0
    
    @api.constrains('merchant_id')
    def _check_merchant_id(self):
        for acquirer in self:
            if self.search_count([
                ('merchant_id', '=', acquirer.merchant_id),
                ('environment', '=', acquirer.environment),
                ('id', '!=', acquirer.id)
            ]):
                raise ValidationError(_(
                    'Merchant ID must be unique per environment!'
                ))
    
    def action_test_connection(self):
        """Test connection to Geidea API"""
        self.ensure_one()
        try:
            response = self._make_api_request('GET', '/merchant/status')
            if response.get('success'):
                self.state = 'active'
                self.message_post(body=_("Connection test successful"))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Connection test successful!'),
                        'type': 'success',
                    }
                }
            else:
                raise ValidationError(_("Connection test failed: %s") % response.get('message'))
        except Exception as e:
            self.state = 'error'
            self.message_post(body=_("Connection test failed: %s") % str(e))
            raise ValidationError(_("Connection test failed: %s") % str(e))
    
    def action_activate(self):
        """Activate the acquirer"""
        self.ensure_one()
        self.action_test_connection()
        self.state = 'active'
    
    def action_deactivate(self):
        """Deactivate the acquirer"""
        self.ensure_one()
        self.state = 'inactive'
    
    def _get_api_url(self):
        """Get the appropriate API URL based on environment"""
        return self.api_url_production if self.environment == 'production' else self.api_url_test
    
    def _get_api_headers(self):
        """Get API headers for Geidea requests"""
        return {
            'Authorization': f"Bearer {self._decrypt_sensitive_data(self.api_key)}",
            'Content-Type': 'application/json',
            'X-Merchant-Id': self.merchant_id,
        }
    
    def _make_api_request(self, method, endpoint, data=None, timeout=30):
        """Make a request to Geidea API"""
        url = f"{self._get_api_url()}{endpoint}"
        headers = self._get_api_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error("Geidea API request failed: %s", str(e))
            raise
    
    def create_payment_transaction(self, amount, currency, order_ref, customer_data=None):
        """Create a payment transaction through Geidea API"""
        self.ensure_one()
        
        payload = {
            'amount': amount,
            'currency': currency.name,
            'merchantId': self.merchant_id,
            'orderId': order_ref,
            'customer': customer_data or {},
            'isTest': self.environment == 'test',
            'autoCapture': self.auto_capture,
        }
        
        try:
            response = self._make_api_request('POST', '/payment/create', payload)
            return response
        except Exception as e:
            _logger.error("Failed to create payment transaction: %s", str(e))
            raise
    
    def capture_payment(self, transaction_id, amount=None):
        """Capture a payment transaction"""
        self.ensure_one()
        
        payload = {
            'transactionId': transaction_id,
            'merchantId': self.merchant_id,
        }
        
        if amount:
            payload['amount'] = amount
        
        try:
            response = self._make_api_request('POST', '/payment/capture', payload)
            return response
        except Exception as e:
            _logger.error("Failed to capture payment: %s", str(e))
            raise
    
    def refund_payment(self, transaction_id, amount, reason=None):
        """Refund a payment transaction"""
        self.ensure_one()
        
        payload = {
            'transactionId': transaction_id,
            'amount': amount,
            'merchantId': self.merchant_id,
            'reason': reason or 'Customer request',
        }
        
        try:
            response = self._make_api_request('POST', '/payment/refund', payload)
            return response
        except Exception as e:
            _logger.error("Failed to refund payment: %s", str(e))
            raise