# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError



_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Geidea-specific fields
    geidea_transaction_id = fields.Char(
        string='Geidea Transaction ID',
        readonly=True,
        help='Transaction ID from Geidea payment gateway'
    )
    geidea_order_id = fields.Char(
        string='Geidea Order ID',
        readonly=True,
        help='Order ID from Geidea payment gateway'
    )
    geidea_payment_method = fields.Char(
        string='Payment Method',
        readonly=True,
        help='Payment method used in Geidea (Card, Wallet, etc.)'
    )
    geidea_card_last4 = fields.Char(
        string='Card Last 4 Digits',
        readonly=True,
        help='Last 4 digits of the card used'
    )
    geidea_response_code = fields.Char(
        string='Response Code',
        readonly=True,
        help='Response code from Geidea gateway'
    )
    geidea_response_message = fields.Text(
        string='Response Message',
        readonly=True,
        help='Response message from Geidea gateway'
    )

    def _get_specific_rendering_values(self, processing_values):
        """Return Geidea-specific rendering values"""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'geidea':
            return res

        # Prepare Geidea payment data
        payment_data = {
            'merchantId': self.provider_id.geidea_merchant_id,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'orderId': self.reference,
            'returnUrl': processing_values.get('return_url'),
            'callbackUrl': processing_values.get('webhook_url'),
            'customer': {
                'email': self.partner_email or '',
                'phone': self.partner_phone or '',
            },
            'language': self._get_geidea_language(),
        }

        # Add billing details if available
        if self.partner_id:
            payment_data['billing'] = {
                'name': self.partner_name or '',
                'address': {
                    'street': self.partner_address or '',
                    'city': self.partner_city or '',
                    'country': self.partner_country_id.code or '',
                }
            }

        res.update({
            'api_url': self.provider_id._geidea_get_api_url('checkout/payment'),
            'payment_data': payment_data,
        })
        return res

    def _get_geidea_language(self):
        """Get language code for Geidea (en or ar)"""
        lang = self.env.context.get('lang', 'en_US')
        return 'ar' if lang.startswith('ar') else 'en'

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find transaction from Geidea notification data"""
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'geidea' or len(tx) == 1:
            return tx

        # Look for transaction by Geidea transaction ID or order ID
        geidea_tx_id = notification_data.get('transactionId')
        order_id = notification_data.get('orderId')
        
        if geidea_tx_id:
            tx = self.search([('geidea_transaction_id', '=', geidea_tx_id)])
        elif order_id:
            tx = self.search([('reference', '=', order_id)])
            
        if not tx:
            raise ValidationError(
                f"Geidea: No transaction found with transaction ID {geidea_tx_id} or order ID {order_id}"
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Process Geidea notification data"""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'geidea':
            return

        # Update Geidea-specific fields
        self.geidea_transaction_id = notification_data.get('transactionId')
        self.geidea_order_id = notification_data.get('orderId')
        self.geidea_payment_method = notification_data.get('paymentMethod', {}).get('type')
        
        # Extract card information if available
        payment_method = notification_data.get('paymentMethod', {})
        if payment_method.get('type') == 'card':
            card_info = payment_method.get('card', {})
            self.geidea_card_last4 = card_info.get('maskedCardNumber', '')[-4:] if card_info.get('maskedCardNumber') else ''

        # Update response information
        self.geidea_response_code = notification_data.get('responseCode')
        self.geidea_response_message = notification_data.get('responseMessage')

        # Determine transaction state
        response_code = notification_data.get('responseCode')
        status = notification_data.get('status', '').lower()
        
        if response_code == '000' and status == 'success':
            self._set_done()
        elif status in ['failed', 'cancelled']:
            self._set_canceled()
        else:
            self._set_pending()

    def _send_payment_request(self):
        """Send payment request to Geidea"""
        if self.provider_code != 'geidea':
            return super()._send_payment_request()

        # Prepare payment request data
        payment_data = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'merchantReferenceId': self.reference,
            'callbackUrl': self._get_base_url() + '/payment/geidea/webhook',
            'returnUrl': self._get_base_url() + '/payment/geidea/return',
            'customer': {
                'email': self.partner_email or '',
                'phoneNumber': self.partner_phone or '',
            },
            'language': self._get_geidea_language(),
        }

        # Add billing information
        if self.partner_id:
            payment_data['billing'] = {
                'firstName': self.partner_name.split(' ')[0] if self.partner_name else '',
                'lastName': ' '.join(self.partner_name.split(' ')[1:]) if self.partner_name and ' ' in self.partner_name else '',
                'address': {
                    'street1': self.partner_address or '',
                    'city': self.partner_city or '',
                    'countryCode': self.partner_country_id.code or '',
                }
            }

        try:
            response = self.provider_id._geidea_make_request('checkout/payment', payment_data)
            
            # Update transaction with response data
            if response.get('orderId'):
                self.geidea_order_id = response['orderId']
            if response.get('transactionId'):
                self.geidea_transaction_id = response['transactionId']
                
            # Return redirect URL if provided
            return response.get('redirectUrl')
            
        except Exception as e:
            _logger.error(f"Geidea payment request failed: {str(e)}")
            raise UserError(_("Payment request failed. Please try again."))

    def _send_refund_request(self, amount_to_refund=None):
        """Send refund request to Geidea"""
        if self.provider_code != 'geidea':
            return super()._send_refund_request(amount_to_refund)

        refund_amount = amount_to_refund or self.amount
        
        refund_data = {
            'transactionId': self.geidea_transaction_id,
            'amount': refund_amount,
            'currency': self.currency_id.name,
            'reason': 'Customer request',
        }

        try:
            response = self.provider_id._geidea_make_request('transactions/refund', refund_data)
            
            # Create refund transaction
            refund_tx = self._create_refund_transaction(amount_to_refund)
            if response.get('transactionId'):
                refund_tx.geidea_transaction_id = response['transactionId']
                
            return refund_tx
            
        except Exception as e:
            _logger.error(f"Geidea refund request failed: {str(e)}")
            raise UserError(_("Refund request failed. Please try again."))

    def _create_refund_transaction(self, amount_to_refund=None):
        """Create a refund transaction"""
        refund_amount = amount_to_refund or self.amount
        
        return self.create({
            'reference': f"{self.reference}-refund-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'provider_id': self.provider_id.id,
            'provider_reference': self.provider_reference,
            'amount': -refund_amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'operation': 'refund',
            'source_transaction_id': self.id,
        })