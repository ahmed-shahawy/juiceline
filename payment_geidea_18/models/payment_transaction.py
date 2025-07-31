# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    geidea_transaction_id = fields.Char(
        string='Geidea Transaction ID',
        help='Transaction ID returned by Geidea',
        readonly=True
    )

    def _get_specific_rendering_values(self, processing_values):
        """Override to return Geidea-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'geidea':
            return res

        # Add Geidea specific rendering values
        geidea_values = {
            'merchant_key': self.provider_id.geidea_merchant_key,
            'merchant_public_key': self.provider_id.geidea_merchant_public_key,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'reference': self.reference,
            'return_url': processing_values.get('return_url'),
        }
        
        return geidea_values

    def _process_notification_data(self, notification_data):
        """Override to process Geidea notification data."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'geidea':
            return

        # Process Geidea specific notification data
        self.geidea_transaction_id = notification_data.get('transactionId')
        
        # Update transaction state based on Geidea response
        status = notification_data.get('status')
        if status == 'success':
            self._set_done()
        elif status == 'failed':
            self._set_error("Payment failed")
        elif status == 'cancelled':
            self._set_canceled()