# -*- coding: utf-8 -*-

import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):

    _return_url = '/payment/geidea/return/<int:tx_id>'
    _webhook_url = '/payment/geidea/webhook'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def geidea_return_from_checkout(self, tx_id, **data):
        """Handle the return from Geidea checkout."""
        _logger.info("Geidea return data for transaction %s:\n%s", tx_id, pprint.pformat(data))

        # Fetch the transaction
        tx_sudo = request.env['payment.transaction'].sudo().browse(tx_id)
        if not tx_sudo.exists():
            raise ValidationError("Geidea: Transaction not found.")

        # Process the return data
        try:
            tx_sudo._process_notification_data(data)
        except ValidationError as e:
            _logger.exception("Geidea: Error processing return data")
            tx_sudo._set_error(str(e))

        # Redirect to the appropriate page
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_webhook(self, **data):
        """Handle Geidea webhook notifications."""
        _logger.info("Geidea webhook data:\n%s", pprint.pformat(data))

        try:
            # Verify the webhook authenticity (implement signature verification if available)
            if not self._verify_geidea_webhook(data):
                _logger.warning("Geidea: Invalid webhook signature")
                return http.Response(status=400)

            # Find the transaction
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'geidea', data
            )

            # Process the notification
            tx_sudo._process_notification_data(data)
            tx_sudo._execute_callback()

            return http.Response(status=200)
        except Exception as e:
            _logger.exception("Geidea: Error processing webhook")
            return http.Response(status=500)

    def _verify_geidea_webhook(self, data):
        """Verify the authenticity of the Geidea webhook."""
        # Implement webhook signature verification if Geidea provides it
        # For now, we'll do basic validation
        required_fields = ['orderId', 'transactionId', 'status']
        return all(field in data for field in required_fields)

    @http.route('/payment/geidea/test', type='http', auth='user', methods=['GET'])
    def geidea_test_connection(self):
        """Test endpoint for Geidea API connection (development only)."""
        if not request.env.user.has_group('base.group_system'):
            return request.redirect('/web')

        try:
            provider = request.env['payment.provider'].search([('code', '=', 'geidea')], limit=1)
            if not provider:
                return "No Geidea provider configured"

            # Test API connection
            result = provider._geidea_make_request('/v1/health', method='GET')
            return f"Geidea API connection successful: {result}"
        except Exception as e:
            return f"Geidea API connection failed: {str(e)}"