# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class GeideaTransaction(models.Model):
    _name = 'geidea.transaction'
    _description = 'Geidea Payment Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Transaction Reference',
        required=True,
        copy=False,
        default=lambda self: _('New')
    )
    
    transaction_id = fields.Char(
        string='Geidea Transaction ID',
        help="Unique transaction ID from Geidea gateway"
    )
    
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error')
    ], string='Status', default='draft', tracking=True)
    
    payment_method = fields.Selection([
        ('card', 'Credit/Debit Card'),
        ('contactless', 'Contactless (NFC)'),
        ('digital_wallet', 'Digital Wallet'),
        ('cash', 'Cash')
    ], string='Payment Method', required=True)
    
    device_id = fields.Many2one(
        'geidea.device',
        string='Payment Device',
        required=True
    )
    
    acquirer_id = fields.Many2one(
        'payment.acquirer.geidea',
        string='Payment Acquirer',
        required=True
    )
    
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order'
    )
    
    pos_session_id = fields.Many2one(
        'pos.session',
        string='POS Session'
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer'
    )
    
    card_number = fields.Char(
        string='Card Number (Masked)',
        help="Last 4 digits of the card number"
    )
    
    card_type = fields.Char(
        string='Card Type',
        help="Type of card used (Visa, Mastercard, etc.)"
    )
    
    authorization_code = fields.Char(
        string='Authorization Code',
        help="Authorization code from the payment gateway"
    )
    
    receipt_number = fields.Char(
        string='Receipt Number',
        help="Receipt number for the transaction"
    )
    
    error_message = fields.Text(
        string='Error Message',
        help="Error message in case of failed transaction"
    )
    
    processed_date = fields.Datetime(
        string='Processed Date',
        help="Date and time when transaction was processed"
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('geidea.transaction') or _('New')
        return super(GeideaTransaction, self).create(vals)

    def process_payment(self):
        """Process the payment transaction"""
        self.ensure_one()
        try:
            # Placeholder for actual payment processing logic
            self.state = 'pending'
            self.processed_date = fields.Datetime.now()
            _logger.info(f"Processing payment transaction: {self.name}")
            
            # Simulate successful processing
            self.state = 'authorized'
            self.authorization_code = 'AUTH123456'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Payment processed successfully!"),
                    'type': 'success',
                }
            }
        except Exception as e:
            self.state = 'error'
            self.error_message = str(e)
            _logger.error(f"Payment processing failed for {self.name}: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Payment processing failed: %s") % str(e),
                    'type': 'danger',
                }
            }

    def cancel_transaction(self):
        """Cancel the transaction"""
        self.ensure_one()
        self.state = 'cancelled'
        _logger.info(f"Transaction cancelled: {self.name}")

    def capture_payment(self):
        """Capture authorized payment"""
        self.ensure_one()
        if self.state == 'authorized':
            self.state = 'captured'
            _logger.info(f"Payment captured: {self.name}")
        else:
            raise ValidationError(_("Only authorized payments can be captured"))