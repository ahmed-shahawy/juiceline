# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Override to add Geidea-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'geidea':
            return res

        # Add Geidea-specific values here
        geidea_values = {
            'merchant_id': self.provider_id.geidea_merchant_id,
            'api_key': self.provider_id.geidea_api_key,
            'amount': processing_values['amount'],
            'currency': processing_values['currency'].name,
            'reference': self.reference,
        }
        
        return geidea_values

    def _process_notification_data(self, notification_data):
        """Override to process Geidea notification data."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'geidea':
            return

        # Process Geidea-specific notification data
        _logger.info("Processing Geidea notification for transaction %s", self.reference)

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override to get transaction from Geidea notification data."""
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'geidea' or len(tx) == 1:
            return tx

        # Handle Geidea-specific transaction retrieval
        reference = notification_data.get('orderId')
        if reference:
            tx = self.search([('reference', '=', reference), ('provider_code', '=', 'geidea')])

        return tx