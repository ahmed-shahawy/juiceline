# -*- coding: utf-8 -*-

import logging
import uuid
from werkzeug import urls

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    geidea_transaction_id = fields.Char(
        string="Geidea Transaction ID",
        help="The transaction ID returned by Geidea",
        readonly=True
    )
    geidea_order_id = fields.Char(
        string="Geidea Order ID",
        help="The order ID sent to Geidea",
        readonly=True
    )

    def _get_specific_rendering_values(self, processing_values):
        """Override to provide Geidea-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'geidea':
            return res

        # Generate unique order ID for Geidea
        geidea_order_id = f"OD-{self.reference}-{str(uuid.uuid4())[:8]}"
        
        # Prepare Geidea payment data
        geidea_values = {
            'merchantId': self.provider_id.geidea_merchant_id,
            'orderId': geidea_order_id,
            'amount': str(self.amount),
            'currency': self.currency_id.name,
            'returnUrl': urls.url_join(
                self.provider_id.get_base_url(),
                f'/payment/geidea/return/{self.id}'
            ),
            'callbackUrl': urls.url_join(
                self.provider_id.get_base_url(),
                f'/payment/geidea/webhook'
            ),
            'customerEmail': self.partner_email or '',
            'language': self._get_geidea_language(),
        }

        # Add tokenization if enabled
        if self.provider_id.geidea_enable_tokenization and self.tokenize:
            geidea_values['tokenization'] = True
            if self.token_id:
                geidea_values['tokenId'] = self.token_id.provider_ref

        # Update transaction with Geidea order ID
        self.geidea_order_id = geidea_order_id

        res.update({
            'geidea_values': geidea_values,
            'api_url': self.provider_id._geidea_get_api_url(),
        })
        return res

    def _get_geidea_language(self):
        """Get the appropriate language code for Geidea."""
        lang_code = self.env.context.get('lang', 'en_US')
        if lang_code.startswith('ar'):
            return 'ar'
        return 'en'

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override to handle Geidea notification data."""
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'geidea' or len(tx) == 1:
            return tx

        # Look up transaction by Geidea order ID or transaction ID
        geidea_order_id = notification_data.get('orderId')
        geidea_tx_id = notification_data.get('transactionId')
        
        if geidea_order_id:
            tx = self.search([('geidea_order_id', '=', geidea_order_id)])
        elif geidea_tx_id:
            tx = self.search([('geidea_transaction_id', '=', geidea_tx_id)])

        if not tx:
            raise ValidationError(_(
                "Geidea: No transaction found matching order ID %s or transaction ID %s.",
                geidea_order_id, geidea_tx_id
            ))

        return tx

    def _process_notification_data(self, notification_data):
        """Override to process Geidea notification data."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'geidea':
            return

        # Extract Geidea-specific data
        self.geidea_transaction_id = notification_data.get('transactionId')
        
        # Determine transaction status
        status = notification_data.get('status', '').lower()
        if status == 'success':
            self._set_done()
        elif status in ['failed', 'error', 'declined']:
            self._set_error(_(
                "Payment failed: %s", 
                notification_data.get('responseMessage', 'Unknown error')
            ))
        elif status == 'pending':
            self._set_pending()
        else:
            _logger.warning(
                "Geidea: Unknown transaction status: %s for transaction %s",
                status, self.reference
            )
            self._set_error(_("Unknown payment status: %s") % status)

        # Handle tokenization if enabled
        if self.provider_id.geidea_enable_tokenization and notification_data.get('token'):
            self._geidea_handle_tokenization(notification_data)

    def _geidea_handle_tokenization(self, notification_data):
        """Handle token creation from Geidea response."""
        token_data = notification_data.get('token', {})
        if not token_data:
            return

        # Create or update payment token
        token_vals = {
            'provider_id': self.provider_id.id,
            'partner_id': self.partner_id.id,
            'provider_ref': token_data.get('tokenId'),
            'payment_details': token_data.get('maskedCardNumber', ''),
            'verified': True,
        }

        existing_token = self.env['payment.token'].search([
            ('provider_ref', '=', token_data.get('tokenId')),
            ('provider_id', '=', self.provider_id.id),
            ('partner_id', '=', self.partner_id.id),
        ])

        if existing_token:
            existing_token.write(token_vals)
            self.token_id = existing_token
        else:
            new_token = self.env['payment.token'].create(token_vals)
            self.token_id = new_token