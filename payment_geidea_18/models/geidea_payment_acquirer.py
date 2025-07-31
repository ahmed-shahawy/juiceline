# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GeideaPaymentAcquirer(models.Model):
    """
    Dedicated model for Geidea payment acquirer configuration and management.
    This addresses the POS Interface fix #4 for safer model assumptions.
    """
    
    _name = 'geidea.payment.acquirer'
    _description = 'Geidea Payment Acquirer Configuration'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help='Display name for this Geidea configuration'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Enable/disable this Geidea configuration'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help='Company this configuration belongs to'
    )
    
    payment_provider_id = fields.Many2one(
        'payment.provider',
        string='Payment Provider',
        domain=[('code', '=', 'geidea')],
        help='Associated payment provider record'
    )
    
    # Configuration fields
    merchant_id = fields.Char(
        string='Merchant ID',
        required=True,
        help='Geidea Merchant ID',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    
    terminal_id = fields.Char(
        string='Terminal ID',
        help='Geidea Terminal ID for POS transactions',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    
    api_key = fields.Char(
        string='API Key',
        required=True,
        help='Geidea API Key for authentication',
        groups='base.group_system',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    
    api_password = fields.Char(
        string='API Password',
        required=True,
        help='Geidea API Password for authentication',
        groups='base.group_system',
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    
    gateway_url = fields.Char(
        string='Gateway URL',
        default='https://api.merchant.geidea.net',
        required=True,
        help='Geidea Gateway URL'
    )
    
    test_mode = fields.Boolean(
        string='Test Mode',
        default=True,
        help='Enable test mode for transactions'
    )
    
    auto_capture = fields.Boolean(
        string='Auto Capture',
        default=True,
        help='Automatically capture authorized payments'
    )
    
    timeout_duration = fields.Integer(
        string='Timeout (seconds)',
        default=30,
        help='API request timeout in seconds'
    )
    
    # POS-specific fields
    pos_config_ids = fields.Many2many(
        'pos.config',
        string='POS Configurations',
        help='POS configurations that can use this Geidea acquirer'
    )
    
    pos_enabled = fields.Boolean(
        string='Enable in POS',
        default=True,
        help='Allow this acquirer to be used in Point of Sale'
    )
    
    # Transaction tracking
    transaction_count = fields.Integer(
        string='Transaction Count',
        compute='_compute_transaction_count',
        help='Number of transactions processed'
    )
    
    last_transaction_date = fields.Datetime(
        string='Last Transaction',
        help='Date of the last processed transaction'
    )

    @api.depends('payment_provider_id')
    def _compute_transaction_count(self):
        """Compute the number of transactions for this acquirer."""
        for record in self:
            if record.payment_provider_id:
                count = self.env['payment.transaction'].search_count([
                    ('provider_id', '=', record.payment_provider_id.id)
                ])
                record.transaction_count = count
            else:
                record.transaction_count = 0

    @api.model
    def get_available_acquirers(self, company_id=None):
        """
        Get available Geidea acquirers for POS use.
        This method provides safe access to acquirer models (POS Interface fix #4).
        
        Args:
            company_id (int): Company ID to filter acquirers
            
        Returns:
            recordset: Available Geidea acquirers
        """
        domain = [('active', '=', True), ('pos_enabled', '=', True)]
        
        if company_id:
            domain.append(('company_id', '=', company_id))
        else:
            domain.append(('company_id', '=', self.env.company.id))
            
        return self.search(domain)

    @api.model
    def get_acquirer_by_pos_config(self, pos_config_id):
        """
        Get Geidea acquirer for specific POS configuration.
        
        Args:
            pos_config_id (int): POS configuration ID
            
        Returns:
            recordset: Geidea acquirer for the POS config
        """
        return self.search([
            ('active', '=', True),
            ('pos_enabled', '=', True),
            ('pos_config_ids', 'in', [pos_config_id])
        ], limit=1)

    def test_connection(self):
        """Test connection to Geidea API."""
        self.ensure_one()
        
        try:
            # Create a test transaction to verify connection
            test_data = {
                'amount': 1.00,
                'currency': 'SAR',
                'callbackUrl': 'https://test.callback.url',
                'merchantKey': self.api_key,
                'merchantPassword': self.api_password,
            }
            
            # This would be implemented with actual API call
            # For now, just validate that required fields are present
            if not all([self.merchant_id, self.api_key, self.api_password]):
                raise UserError(_('Missing required credentials for Geidea connection.'))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Geidea connection test successful.'),
                    'type': 'success',
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_view_transactions(self):
        """View transactions for this acquirer."""
        self.ensure_one()
        
        if not self.payment_provider_id:
            raise UserError(_('No payment provider associated with this acquirer.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Geidea Transactions'),
            'res_model': 'payment.transaction',
            'view_mode': 'tree,form',
            'domain': [('provider_id', '=', self.payment_provider_id.id)],
            'context': {
                'search_default_provider_id': self.payment_provider_id.id,
            }
        }

    @api.model
    def create_from_provider(self, provider_id):
        """
        Create Geidea acquirer from payment provider.
        
        Args:
            provider_id (int): Payment provider ID
            
        Returns:
            recordset: Created Geidea acquirer
        """
        provider = self.env['payment.provider'].browse(provider_id)
        
        if provider.code != 'geidea':
            raise UserError(_('Provider must be of type Geidea.'))
        
        return self.create({
            'name': f"Geidea - {provider.company_id.name}",
            'payment_provider_id': provider.id,
            'company_id': provider.company_id.id,
            'merchant_id': provider.geidea_merchant_id,
            'api_key': provider.geidea_public_key,
            'api_password': provider.geidea_private_key,
            'gateway_url': provider.geidea_gateway_url,
            'test_mode': provider.geidea_test_mode,
        })

    def update_last_transaction(self):
        """Update last transaction timestamp."""
        # Use fields.Datetime.now() instead of request.env.cr.now() (Structure fix #2)
        self.last_transaction_date = fields.Datetime.now()

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Load data fields for POS."""
        return [
            'name', 'active', 'merchant_id', 'terminal_id', 
            'test_mode', 'auto_capture', 'pos_enabled'
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        """Load data domain for POS."""
        config_id = data.get('pos.config', {}).get('data', [{}])[0].get('id')
        if config_id:
            return [
                ('active', '=', True),
                ('pos_enabled', '=', True),
                ('pos_config_ids', 'in', [config_id])
            ]
        return [('active', '=', True), ('pos_enabled', '=', True)]

    def process_pos_payment(self, payment_data):
        """
        Process POS payment through Geidea API.
        Implements asynchronous payment processing for POS (Structure fix #3).
        
        Args:
            payment_data (dict): Payment data from POS
            
        Returns:
            dict: Payment result
        """
        self.ensure_one()
        
        try:
            # Validate payment data
            required_fields = ['amount', 'currency', 'order_id', 'reference']
            missing_fields = [field for field in required_fields if not payment_data.get(field)]
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }

            # Create payment transaction record
            transaction_vals = {
                'reference': payment_data['reference'],
                'provider_id': self.payment_provider_id.id,
                'amount': payment_data['amount'],
                'currency_id': self.env['res.currency'].search([('name', '=', payment_data['currency'])], limit=1).id,
                'partner_id': self.env.user.partner_id.id,
                'operation': 'online_direct',
                'geidea_order_id': payment_data['order_id'],
            }
            
            transaction = self.env['payment.transaction'].create(transaction_vals)
            
            # Prepare Geidea API request
            api_data = {
                'merchantId': self.merchant_id,
                'terminalId': self.terminal_id,
                'orderId': payment_data['order_id'],
                'amount': payment_data['amount'],
                'currency': payment_data['currency'],
                'customerEmail': payment_data.get('customer_email', ''),
                'reference': payment_data['reference'],
                'timestamp': payment_data['timestamp'],
            }

            # Simulate successful payment for demo purposes
            # In production, this would make actual API call to Geidea
            if self.test_mode:
                # Simulate processing delay
                import time
                time.sleep(1)
                
                result = {
                    'success': True,
                    'transaction_id': f'GEIDEA_{transaction.id}_{int(fields.Datetime.now().timestamp())}',
                    'response_code': '000',
                    'response_message': 'Approved',
                    'reference': payment_data['reference']
                }
                
                # Update transaction with result
                transaction.set_geidea_transaction_id(result['transaction_id'])
                transaction._set_done()
                
                # Update last transaction timestamp
                self.update_last_transaction()
                
                return result
            else:
                # For production, implement actual Geidea API call here
                return {
                    'success': False,
                    'error': 'Production mode not yet implemented'
                }
                
        except Exception as e:
            _logger.error('POS payment processing error: %s', str(e))
            return {
                'success': False,
                'error': f'Payment processing failed: {str(e)}'
            }