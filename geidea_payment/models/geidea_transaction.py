# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class GeideaTransaction(models.Model):
    _name = 'geidea.transaction'
    _description = 'Geidea Payment Transaction'
    _order = 'create_date desc'
    _rec_name = 'transaction_id'

    transaction_id = fields.Char(
        string='Transaction ID',
        required=True,
        copy=False,
        help='Unique transaction identifier from Geidea'
    )
    
    payment_transaction_id = fields.Many2one(
        'payment.transaction',
        string='Payment Transaction',
        help='Related Odoo payment transaction'
    )
    
    provider_id = fields.Many2one(
        'payment.provider',
        string='Payment Provider',
        domain=[('code', '=', 'geidea')],
        required=True
    )
    
    device_id = fields.Many2one(
        'geidea.device',
        string='Device',
        help='Device used for this transaction'
    )
    
    # Transaction details
    amount = fields.Monetary(
        string='Amount',
        required=True,
        help='Transaction amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], string='State', default='draft', required=True)
    
    # Geidea specific fields
    geidea_order_id = fields.Char(
        string='Geidea Order ID',
        help='Order ID from Geidea system'
    )
    
    geidea_payment_id = fields.Char(
        string='Geidea Payment ID',
        help='Payment ID from Geidea system'
    )
    
    authorization_code = fields.Char(
        string='Authorization Code',
        help='Authorization code from payment processor'
    )
    
    response_code = fields.Char(
        string='Response Code',
        help='Response code from Geidea'
    )
    
    response_message = fields.Text(
        string='Response Message',
        help='Response message from Geidea'
    )
    
    # Timestamps
    initiated_date = fields.Datetime(
        string='Initiated Date',
        default=fields.Datetime.now,
        help='When transaction was initiated'
    )
    
    processed_date = fields.Datetime(
        string='Processed Date',
        help='When transaction was processed by Geidea'
    )
    
    # Customer information
    customer_email = fields.Char(string='Customer Email')
    customer_phone = fields.Char(string='Customer Phone')
    
    # Additional data
    raw_data = fields.Text(
        string='Raw Response Data',
        help='Raw response data from Geidea for debugging'
    )
    
    @api.model
    def create_from_geidea_response(self, response_data, provider_id, device_id=None):
        """Create transaction record from Geidea response"""
        vals = {
            'transaction_id': response_data.get('transactionId'),
            'provider_id': provider_id,
            'device_id': device_id,
            'amount': response_data.get('amount', 0.0),
            'geidea_order_id': response_data.get('orderId'),
            'geidea_payment_id': response_data.get('paymentId'),
            'authorization_code': response_data.get('authCode'),
            'response_code': response_data.get('responseCode'),
            'response_message': response_data.get('responseMessage'),
            'raw_data': str(response_data),
        }
        
        # Set state based on response
        if response_data.get('responseCode') == '000':
            vals['state'] = 'authorized'
        else:
            vals['state'] = 'failed'
            
        return self.create(vals)
    
    def _process_webhook_data(self, webhook_data):
        """Process webhook data and update transaction"""
        self.ensure_one()
        
        # Update transaction based on webhook
        state_mapping = {
            'AUTHORIZED': 'authorized',
            'CAPTURED': 'captured',
            'CANCELLED': 'cancelled',
            'FAILED': 'failed',
            'REFUNDED': 'refunded'
        }
        
        webhook_state = webhook_data.get('status', '').upper()
        if webhook_state in state_mapping:
            self.state = state_mapping[webhook_state]
        
        # Update additional fields from webhook
        if webhook_data.get('processedDate'):
            self.processed_date = webhook_data['processedDate']
        
        if webhook_data.get('authCode'):
            self.authorization_code = webhook_data['authCode']
        
        # Update raw data
        self.raw_data = str(webhook_data)