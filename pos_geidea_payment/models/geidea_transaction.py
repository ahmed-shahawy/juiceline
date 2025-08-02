# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)


class GeideaTransaction(models.Model):
    _name = 'geidea.transaction'
    _description = 'Geidea Payment Transaction'
    _order = 'create_date desc'
    _rec_name = 'transaction_id'

    # Transaction Identification
    transaction_id = fields.Char(
        string='Transaction ID',
        required=True,
        help='Unique transaction identifier from Geidea'
    )
    
    reference = fields.Char(
        string='Reference',
        help='Merchant reference for this transaction'
    )
    
    order_id = fields.Char(
        string='Order ID',
        help='Associated order identifier'
    )
    
    # Configuration and Device
    config_id = fields.Many2one(
        'geidea.config',
        string='Geidea Configuration',
        required=True,
        ondelete='cascade',
        help='Associated Geidea configuration'
    )
    
    device_id = fields.Many2one(
        'geidea.device',
        string='Payment Device',
        help='Device that processed this transaction'
    )
    
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        help='Associated POS order'
    )
    
    # Transaction Details
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
        help='Transaction amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    type = fields.Selection([
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('authorization', 'Authorization'),
        ('capture', 'Capture'),
        ('void', 'Void')
    ], string='Transaction Type', default='sale', required=True,
       help='Type of transaction')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded')
    ], string='State', default='draft', required=True,
       help='Current transaction state')
    
    # Payment Method Details
    payment_method = fields.Selection([
        ('card', 'Credit/Debit Card'),
        ('contactless', 'Contactless'),
        ('mobile', 'Mobile Payment'),
        ('wallet', 'Digital Wallet'),
        ('other', 'Other')
    ], string='Payment Method',
       help='Method used for payment')
    
    card_type = fields.Selection([
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('other', 'Other')
    ], string='Card Type',
       help='Type of card used')
    
    card_last_four = fields.Char(
        string='Card Last 4 Digits',
        size=4,
        help='Last 4 digits of the card number'
    )
    
    cardholder_name = fields.Char(
        string='Cardholder Name',
        help='Name on the card'
    )
    
    # Transaction Processing
    authorization_code = fields.Char(
        string='Authorization Code',
        help='Authorization code from Geidea'
    )
    
    gateway_transaction_id = fields.Char(
        string='Gateway Transaction ID',
        help='Transaction ID from payment gateway'
    )
    
    rrn = fields.Char(
        string='RRN (Reference Retrieval Number)',
        help='Retrieval reference number'
    )
    
    # Timestamps
    requested_at = fields.Datetime(
        string='Requested At',
        default=fields.Datetime.now,
        help='When the transaction was requested'
    )
    
    processed_at = fields.Datetime(
        string='Processed At',
        help='When the transaction was processed'
    )
    
    completed_at = fields.Datetime(
        string='Completed At',
        help='When the transaction was completed'
    )
    
    # Response Data
    response_code = fields.Char(
        string='Response Code',
        help='Response code from Geidea'
    )
    
    response_message = fields.Text(
        string='Response Message',
        help='Response message from Geidea'
    )
    
    raw_response = fields.Text(
        string='Raw Response',
        help='Raw response data from Geidea API'
    )
    
    # Error Handling
    error_code = fields.Char(
        string='Error Code',
        help='Error code if transaction failed'
    )
    
    error_message = fields.Text(
        string='Error Message',
        help='Error message if transaction failed'
    )
    
    # Customer Information
    customer_email = fields.Char(
        string='Customer Email',
        help='Customer email address'
    )
    
    customer_phone = fields.Char(
        string='Customer Phone',
        help='Customer phone number'
    )
    
    # Additional Data
    metadata = fields.Text(
        string='Metadata',
        help='Additional transaction metadata in JSON format'
    )
    
    receipt_data = fields.Text(
        string='Receipt Data',
        help='Receipt data in JSON format'
    )
    
    # Relationship fields
    parent_transaction_id = fields.Many2one(
        'geidea.transaction',
        string='Parent Transaction',
        help='Parent transaction for refunds/voids'
    )
    
    child_transaction_ids = fields.One2many(
        'geidea.transaction',
        'parent_transaction_id',
        string='Child Transactions',
        help='Related transactions (refunds, voids, etc.)'
    )
    
    # Computed fields
    is_refundable = fields.Boolean(
        string='Is Refundable',
        compute='_compute_is_refundable',
        help='Whether this transaction can be refunded'
    )
    
    refunded_amount = fields.Monetary(
        string='Refunded Amount',
        compute='_compute_refunded_amount',
        currency_field='currency_id',
        help='Total amount that has been refunded'
    )
    
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        compute='_compute_remaining_amount',
        currency_field='currency_id',
        help='Amount that can still be refunded'
    )

    @api.depends('state', 'type', 'completed_at')
    def _compute_is_refundable(self):
        """Compute if transaction is refundable"""
        for transaction in self:
            transaction.is_refundable = (
                transaction.state == 'completed' and
                transaction.type == 'sale' and
                transaction.completed_at and
                transaction.amount > 0
            )

    @api.depends('child_transaction_ids.amount', 'child_transaction_ids.state')
    def _compute_refunded_amount(self):
        """Compute total refunded amount"""
        for transaction in self:
            refunds = transaction.child_transaction_ids.filtered(
                lambda t: t.type == 'refund' and t.state == 'completed'
            )
            transaction.refunded_amount = sum(refunds.mapped('amount'))

    @api.depends('amount', 'refunded_amount')
    def _compute_remaining_amount(self):
        """Compute remaining amount that can be refunded"""
        for transaction in self:
            transaction.remaining_amount = transaction.amount - transaction.refunded_amount

    @api.constrains('card_last_four')
    def _check_card_last_four(self):
        """Validate card last four digits"""
        for transaction in self:
            if transaction.card_last_four:
                if not transaction.card_last_four.isdigit() or len(transaction.card_last_four) != 4:
                    raise ValidationError(_('Card last four digits must be exactly 4 digits'))

    @api.constrains('amount')
    def _check_amount(self):
        """Validate transaction amount"""
        for transaction in self:
            if transaction.amount <= 0:
                raise ValidationError(_('Transaction amount must be positive'))

    def action_process(self):
        """Process the transaction"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Only draft transactions can be processed'))
        
        try:
            self.state = 'processing'
            self.processed_at = fields.Datetime.now()
            
            # Implementation for processing transaction with Geidea API
            # This would make the actual API call
            
            # Simulate successful processing
            self.state = 'completed'
            self.completed_at = fields.Datetime.now()
            self.response_code = '00'
            self.response_message = 'Transaction approved'
            self.authorization_code = 'AUTH123456'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Transaction Processed'),
                    'message': _('Transaction %s processed successfully') % self.transaction_id,
                    'type': 'success',
                }
            }
        except Exception as e:
            self.state = 'failed'
            self.error_message = str(e)
            raise ValidationError(_('Transaction processing failed: %s') % str(e))

    def action_refund(self, refund_amount=None):
        """Refund the transaction"""
        self.ensure_one()
        
        if not self.is_refundable:
            raise ValidationError(_('This transaction cannot be refunded'))
        
        if refund_amount is None:
            refund_amount = self.remaining_amount
        
        if refund_amount <= 0 or refund_amount > self.remaining_amount:
            raise ValidationError(_('Invalid refund amount'))
        
        try:
            # Create refund transaction
            refund_transaction = self.create({
                'transaction_id': 'REF_%s_%s' % (self.transaction_id, fields.Datetime.now().strftime('%Y%m%d%H%M%S')),
                'reference': 'Refund for %s' % self.reference,
                'config_id': self.config_id.id,
                'device_id': self.device_id.id,
                'amount': refund_amount,
                'currency_id': self.currency_id.id,
                'type': 'refund',
                'state': 'processing',
                'parent_transaction_id': self.id,
                'payment_method': self.payment_method,
                'card_type': self.card_type,
                'card_last_four': self.card_last_four,
                'customer_email': self.customer_email,
                'customer_phone': self.customer_phone,
            })
            
            # Process the refund
            refund_transaction.action_process()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Refund Processed'),
                    'message': _('Refund of %s processed successfully') % refund_amount,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(_('Refund processing failed: %s') % str(e))

    def action_void(self):
        """Void the transaction"""
        self.ensure_one()
        
        if self.state not in ['pending', 'processing']:
            raise ValidationError(_('Only pending or processing transactions can be voided'))
        
        try:
            self.state = 'cancelled'
            self.response_message = 'Transaction voided'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Transaction Voided'),
                    'message': _('Transaction %s has been voided') % self.transaction_id,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(_('Transaction void failed: %s') % str(e))

    @api.model
    def create_from_pos_payment(self, pos_payment_data):
        """Create transaction from POS payment data"""
        return self.create({
            'transaction_id': pos_payment_data.get('transaction_id'),
            'reference': pos_payment_data.get('reference'),
            'order_id': pos_payment_data.get('order_id'),
            'amount': pos_payment_data.get('amount'),
            'currency_id': pos_payment_data.get('currency_id'),
            'config_id': pos_payment_data.get('config_id'),
            'device_id': pos_payment_data.get('device_id'),
            'payment_method': pos_payment_data.get('payment_method'),
            'customer_email': pos_payment_data.get('customer_email'),
            'customer_phone': pos_payment_data.get('customer_phone'),
            'metadata': json.dumps(pos_payment_data.get('metadata', {})),
        })

    def get_receipt_data(self):
        """Get formatted receipt data"""
        self.ensure_one()
        
        receipt_data = {
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'card_last_four': self.card_last_four,
            'card_type': self.card_type,
            'authorization_code': self.authorization_code,
            'processed_at': self.processed_at,
            'merchant_id': self.config_id.merchant_id,
            'terminal_id': self.config_id.terminal_id,
        }
        
        return receipt_data