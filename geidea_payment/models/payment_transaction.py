# -*- coding: utf-8 -*-
import logging
from dateutil import parser

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Geidea specific fields
    geidea_transaction_id = fields.Char(
        string='Geidea Transaction ID',
        help='Unique transaction ID from Geidea',
        readonly=True
    )
    geidea_session_id = fields.Char(
        string='Geidea Session ID',
        help='Payment session ID from Geidea',
        readonly=True
    )
    geidea_response_code = fields.Char(
        string='Response Code',
        help='Response code from Geidea gateway',
        readonly=True
    )
    geidea_response_message = fields.Text(
        string='Response Message',
        help='Response message from Geidea gateway',
        readonly=True
    )
    geidea_payment_method = fields.Char(
        string='Payment Method',
        help='Payment method used (Card, Wallet, etc.)',
        readonly=True
    )
    geidea_card_last4 = fields.Char(
        string='Card Last 4 Digits',
        help='Last 4 digits of the card used',
        readonly=True
    )
    geidea_card_brand = fields.Char(
        string='Card Brand',
        help='Brand of the card used (Visa, Mastercard, etc.)',
        readonly=True
    )

    def _get_specific_rendering_values(self, processing_values):
        """Override to provide Geidea-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'geidea':
            return res

        # Generate Geidea payment form values
        payment_values = self.acquirer_id.geidea_form_generate_values({
            'amount': self.amount,
            'currency': self.currency_id,
            'reference': self.reference,
            'return_url': processing_values.get('return_url'),
            'partner_email': self.partner_email,
            'partner_phone': self.partner_phone,
            'partner_lang': self.partner_lang,
            'billing_partner_name': self.partner_name,
            'billing_partner_city': self.partner_city,
            'billing_partner_country': self.partner_country_id,
            'billing_partner_address': self.partner_address,
            'billing_partner_zip': self.partner_zip,
        })

        return {
            'api_url': self.acquirer_id.geidea_get_form_action_url(),
            'payment_data': payment_values,
        }

    def _get_tx_from_feedback_data(self, provider, data):
        """Find transaction from Geidea feedback data."""
        if provider != 'geidea':
            return super()._get_tx_from_feedback_data(provider, data)

        reference = data.get('merchantReferenceId')
        geidea_txn_id = data.get('transactionId')
        
        if not reference and not geidea_txn_id:
            raise ValidationError('Geidea: Missing transaction reference in feedback data.')

        # Try to find transaction by reference first, then by Geidea transaction ID
        transaction = self.search([('reference', '=', reference)], limit=1)
        if not transaction and geidea_txn_id:
            transaction = self.search([('geidea_transaction_id', '=', geidea_txn_id)], limit=1)
            
        if not transaction:
            raise ValidationError(f'Geidea: No transaction found for reference {reference}')

        return transaction

    def _process_feedback_data(self, data):
        """Process feedback data from Geidea."""
        super()._process_feedback_data(data)
        
        if self.provider != 'geidea':
            return

        # Update Geidea specific fields
        self.geidea_transaction_id = data.get('transactionId')
        self.geidea_session_id = data.get('sessionId')
        self.geidea_response_code = data.get('responseCode')
        self.geidea_response_message = data.get('responseMessage')
        self.geidea_payment_method = data.get('paymentMethod', {}).get('type')
        
        # Update card information if available
        card_info = data.get('paymentMethod', {}).get('card', {})
        if card_info:
            self.geidea_card_last4 = card_info.get('maskedCardNumber', '')[-4:]
            self.geidea_card_brand = card_info.get('brand')

        # Update transaction state based on Geidea response
        response_code = data.get('responseCode')
        status = data.get('detailedStatus', data.get('status', ''))
        
        if response_code == '000' and status in ['Paid', 'Captured']:
            self._set_done()
            _logger.info('Geidea transaction %s for reference %s: payment successful', 
                        self.geidea_transaction_id, self.reference)
        elif status in ['Cancelled', 'Declined', 'Failed']:
            self._set_canceled()
            _logger.warning('Geidea transaction %s for reference %s: payment failed - %s', 
                           self.geidea_transaction_id, self.reference, 
                           data.get('responseMessage', 'Unknown error'))
        elif status in ['Pending', 'Authorized']:
            self._set_pending()
            _logger.info('Geidea transaction %s for reference %s: payment pending', 
                        self.geidea_transaction_id, self.reference)
        else:
            self._set_error(f"Received unknown status: {status}")
            _logger.error('Geidea transaction %s for reference %s: unknown status %s', 
                         self.geidea_transaction_id, self.reference, status)

    def geidea_refund_transaction(self, amount=None):
        """Process refund through Geidea API."""
        self.ensure_one()
        
        if self.provider != 'geidea':
            raise ValidationError('This method is only for Geidea transactions.')
            
        if self.state != 'done':
            raise ValidationError('Only successful transactions can be refunded.')
            
        if not self.geidea_transaction_id:
            raise ValidationError('Missing Geidea transaction ID for refund.')

        refund_amount = amount or self.amount
        
        # Prepare refund data
        refund_data = {
            'merchantId': self.acquirer_id.geidea_merchant_id,
            'originalTransactionId': self.geidea_transaction_id,
            'amount': refund_amount,
            'currency': self.currency_id.name,
            'reason': f'Refund for order {self.reference}',
            'merchantReferenceId': f'{self.reference}-refund-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
        }

        try:
            # Make refund request to Geidea
            response = self.acquirer_id._geidea_make_request('pgw/api/v1/direct/refund', refund_data)
            
            if response.get('responseCode') == '000':
                # Create refund transaction record
                refund_values = {
                    'acquirer_id': self.acquirer_id.id,
                    'reference': refund_data['merchantReferenceId'],
                    'amount': -refund_amount,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'operation': 'refund',
                    'source_transaction_id': self.id,
                    'geidea_transaction_id': response.get('transactionId'),
                    'state': 'done',
                }
                
                refund_tx = self.create(refund_values)
                _logger.info('Geidea refund successful for transaction %s, refund ID: %s', 
                           self.geidea_transaction_id, response.get('transactionId'))
                return refund_tx
            else:
                error_msg = response.get('responseMessage', 'Unknown error during refund')
                _logger.error('Geidea refund failed for transaction %s: %s', 
                            self.geidea_transaction_id, error_msg)
                raise ValidationError(f'Refund failed: {error_msg}')
                
        except Exception as e:
            _logger.error('Error processing Geidea refund for transaction %s: %s', 
                         self.geidea_transaction_id, str(e))
            raise ValidationError(f'Refund processing failed: {str(e)}')

    def geidea_check_transaction_status(self):
        """Check transaction status with Geidea API."""
        self.ensure_one()
        
        if self.provider != 'geidea':
            return False
            
        if not self.geidea_transaction_id:
            return False

        try:
            inquiry_data = {
                'merchantId': self.acquirer_id.geidea_merchant_id,
                'transactionId': self.geidea_transaction_id,
            }
            
            response = self.acquirer_id._geidea_make_request(
                'pgw/api/v1/direct/transaction/inquiry', 
                inquiry_data, 
                method='GET'
            )
            
            # Process the response to update transaction status
            self._process_feedback_data(response)
            return True
            
        except Exception as e:
            _logger.error('Error checking Geidea transaction status for %s: %s', 
                         self.geidea_transaction_id, str(e))
            return False