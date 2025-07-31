# -*- coding: utf-8 -*-

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    geidea_transaction_id = fields.Char(
        string="Geidea Transaction ID",
        help="The transaction ID returned by Geidea"
    )

    def _get_specific_rendering_values(self, processing_values):
        """ Override to return Geidea-specific rendering values. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'geidea':
            return res

        # Add Geidea specific rendering values
        rendering_values = {
            'api_url': self.provider_id._geidea_get_api_url(),
            'merchant_id': self.provider_id.geidea_merchant_id,
            'terminal_id': self.provider_id.geidea_terminal_id,
            'api_key': self.provider_id.geidea_api_key,
        }
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override to find the transaction based on Geidea notification data. """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'geidea' or len(tx) == 1:
            return tx

        # Look for transaction using Geidea transaction ID
        geidea_tx_id = notification_data.get('orderId')
        if geidea_tx_id:
            tx = self.search([('geidea_transaction_id', '=', geidea_tx_id)])
        
        return tx

    def _process_notification_data(self, notification_data):
        """ Override to process Geidea notification data. """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'geidea':
            return

        # Store Geidea transaction ID
        self.geidea_transaction_id = notification_data.get('orderId')
        
        # Process payment status
        payment_status = notification_data.get('status')
        if payment_status == 'SUCCESS':
            self._set_done()
        elif payment_status == 'FAILED':
            self._set_error("Payment failed")
        elif payment_status == 'PENDING':
            self._set_pending()
        else:
            _logger.warning("Received unknown payment status: %s", payment_status)
            self._set_error("Unknown payment status")