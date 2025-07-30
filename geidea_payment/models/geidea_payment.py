# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class GeideaPayment(models.Model):
    _name = 'geidea.payment'
    _description = 'Geidea Payment Transaction'
    _rec_name = 'transaction_id'
    _order = 'create_date desc'

    transaction_id = fields.Char(
        string='Transaction ID',
        required=True,
        readonly=True,
        help='Unique transaction identifier from Geidea'
    )
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        readonly=True,
        help='Related POS order'
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        readonly=True,
        help='Transaction amount'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
        default=lambda self: self.env.company.currency_id
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', readonly=True)
    
    payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Payment Method',
        readonly=True
    )
    reference = fields.Char(
        string='Reference',
        readonly=True,
        help='Order reference'
    )
    error_message = fields.Text(
        string='Error Message',
        readonly=True,
        help='Error details if transaction failed'
    )
    response_data = fields.Text(
        string='Response Data',
        readonly=True,
        help='Full response from Geidea API'
    )
    
    @api.model
    def create_transaction(self, values):
        """Create a new Geidea payment transaction"""
        transaction = self.create(values)
        _logger.info(f'Created Geidea transaction {transaction.transaction_id} for amount {transaction.amount}')
        return transaction
    
    def mark_success(self, response_data=None):
        """Mark transaction as successful"""
        self.ensure_one()
        self.write({
            'state': 'success',
            'response_data': response_data or ''
        })
        _logger.info(f'Geidea transaction {self.transaction_id} marked as successful')
    
    def mark_failed(self, error_message, response_data=None):
        """Mark transaction as failed"""
        self.ensure_one()
        self.write({
            'state': 'failed',
            'error_message': error_message,
            'response_data': response_data or ''
        })
        _logger.warning(f'Geidea transaction {self.transaction_id} failed: {error_message}')
    
    def cancel_transaction(self):
        """Cancel the transaction"""
        self.ensure_one()
        if self.state == 'success':
            raise UserError(_('Cannot cancel a successful transaction'))
        
        self.write({'state': 'cancelled'})
        _logger.info(f'Geidea transaction {self.transaction_id} cancelled')