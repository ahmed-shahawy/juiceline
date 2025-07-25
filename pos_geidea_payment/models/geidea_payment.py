# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import json
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class GeideaPayment(models.Model):
    _name = 'geidea.payment'
    _description = 'Geidea Payment Transaction'
    _order = 'create_date desc'
    _rec_name = 'transaction_id'

    # Transaction identification
    transaction_id = fields.Char(
        string="Transaction ID",
        required=True,
        copy=False,
        help="Unique transaction identifier from Geidea"
    )
    
    reference = fields.Char(
        string="Reference",
        required=True,
        help="Internal reference for the transaction"
    )
    
    # Order relationship
    pos_order_id = fields.Many2one(
        'pos.order',
        string="POS Order",
        ondelete='cascade',
        help="Related POS order"
    )
    
    pos_session_id = fields.Many2one(
        'pos.session',
        string="POS Session",
        required=True,
        help="POS session where transaction occurred"
    )
    
    # Transaction details
    amount = fields.Monetary(
        string="Amount",
        required=True,
        currency_field='currency_id',
        help="Transaction amount"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        required=True,
        help="Transaction currency"
    )
    
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
        ('partially_refunded', 'Partially Refunded'),
    ], string="Status", default='draft', required=True, help="Transaction status")
    
    # Payment method details
    payment_method = fields.Selection([
        ('card', 'Credit/Debit Card'),
        ('digital_wallet', 'Digital Wallet'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ], string="Payment Method", help="Payment method used")
    
    card_type = fields.Char(
        string="Card Type",
        help="Type of card used (Visa, Mastercard, etc.)"
    )
    
    last_four_digits = fields.Char(
        string="Last 4 Digits",
        size=4,
        help="Last 4 digits of the card"
    )
    
    # Device and connection info
    device_id = fields.Char(
        string="Device ID",
        help="ID of the payment device used"
    )
    
    bluetooth_mac = fields.Char(
        string="Bluetooth MAC",
        help="MAC address of the Bluetooth device"
    )
    
    connection_type = fields.Selection([
        ('bluetooth', 'Bluetooth'),
        ('wifi', 'WiFi'),
        ('usb', 'USB'),
        ('ethernet', 'Ethernet'),
    ], string="Connection Type", default='bluetooth', help="Type of connection used")
    
    # iOS specific fields
    ios_device_id = fields.Char(
        string="iOS Device ID",
        help="iOS device identifier"
    )
    
    ios_app_state = fields.Selection([
        ('foreground', 'Foreground'),
        ('background', 'Background'),
        ('inactive', 'Inactive'),
    ], string="iOS App State", help="State of the iOS app during transaction")
    
    battery_level = fields.Float(
        string="Battery Level (%)",
        help="iPad battery level during transaction"
    )
    
    # Geidea response data
    geidea_response = fields.Text(
        string="Geidea Response",
        help="Full response from Geidea API"
    )
    
    error_code = fields.Char(
        string="Error Code",
        help="Error code if transaction failed"
    )
    
    error_message = fields.Text(
        string="Error Message",
        help="Error message if transaction failed"
    )
    
    # Timing information
    initiated_at = fields.Datetime(
        string="Initiated At",
        help="When the transaction was initiated"
    )
    
    completed_at = fields.Datetime(
        string="Completed At",
        help="When the transaction was completed"
    )
    
    processing_time = fields.Float(
        string="Processing Time (seconds)",
        compute='_compute_processing_time',
        store=True,
        help="Time taken to process the transaction"
    )
    
    # Refund information
    refund_amount = fields.Monetary(
        string="Refunded Amount",
        currency_field='currency_id',
        default=0.0,
        help="Amount that has been refunded"
    )
    
    refund_transactions = fields.One2many(
        'geidea.payment',
        'original_transaction_id',
        string="Refund Transactions",
        help="Refund transactions for this payment"
    )
    
    original_transaction_id = fields.Many2one(
        'geidea.payment',
        string="Original Transaction",
        help="Original transaction for refunds"
    )
    
    @api.depends('initiated_at', 'completed_at')
    def _compute_processing_time(self):
        for record in self:
            if record.initiated_at and record.completed_at:
                delta = record.completed_at - record.initiated_at
                record.processing_time = delta.total_seconds()
            else:
                record.processing_time = 0.0
    
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("Transaction amount must be positive"))
    
    @api.constrains('refund_amount')
    def _check_refund_amount(self):
        for record in self:
            if record.refund_amount > record.amount:
                raise ValidationError(_("Refund amount cannot exceed original amount"))
    
    def action_authorize(self):
        """Authorize the payment"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_("Can only authorize pending transactions"))
        
        # Here you would implement the actual authorization logic
        self.write({
            'state': 'authorized',
            'initiated_at': fields.Datetime.now(),
        })
        return True
    
    def action_capture(self):
        """Capture the authorized payment"""
        self.ensure_one()
        if self.state != 'authorized':
            raise UserError(_("Can only capture authorized transactions"))
        
        # Here you would implement the actual capture logic
        self.write({
            'state': 'captured',
            'completed_at': fields.Datetime.now(),
        })
        return True
    
    def action_complete(self):
        """Complete the payment"""
        self.ensure_one()
        if self.state not in ['captured', 'processing']:
            raise UserError(_("Can only complete captured or processing transactions"))
        
        self.write({
            'state': 'completed',
            'completed_at': fields.Datetime.now(),
        })
        return True
    
    def action_cancel(self):
        """Cancel the payment"""
        self.ensure_one()
        if self.state in ['completed', 'refunded']:
            raise UserError(_("Cannot cancel completed or refunded transactions"))
        
        self.write({
            'state': 'cancelled',
            'completed_at': fields.Datetime.now(),
        })
        return True
    
    def action_refund(self, refund_amount=None):
        """Refund the payment"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Can only refund completed transactions"))
        
        if refund_amount is None:
            refund_amount = self.amount - self.refund_amount
        
        if refund_amount <= 0:
            raise UserError(_("Refund amount must be positive"))
        
        if refund_amount > (self.amount - self.refund_amount):
            raise UserError(_("Refund amount exceeds available amount"))
        
        # Create refund transaction
        refund_transaction = self.create({
            'transaction_id': f"REF-{self.transaction_id}-{len(self.refund_transactions) + 1}",
            'reference': f"Refund for {self.reference}",
            'pos_order_id': self.pos_order_id.id,
            'pos_session_id': self.pos_session_id.id,
            'amount': -refund_amount,
            'currency_id': self.currency_id.id,
            'state': 'completed',
            'payment_method': self.payment_method,
            'original_transaction_id': self.id,
            'initiated_at': fields.Datetime.now(),
            'completed_at': fields.Datetime.now(),
        })
        
        # Update refunded amount
        new_refund_amount = self.refund_amount + refund_amount
        if new_refund_amount >= self.amount:
            self.state = 'refunded'
        else:
            self.state = 'partially_refunded'
        
        self.refund_amount = new_refund_amount
        
        return refund_transaction