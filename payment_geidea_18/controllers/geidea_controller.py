# -*- coding: utf-8 -*-

import logging
import werkzeug

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):
    _webhook_url = '/payment/geidea/webhook'
    _return_url = '/payment/geidea/return'

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_webhook(self, **data):
        """Process webhook notification from Geidea."""
        _logger.info("Received Geidea webhook with data: %s", data)
        
        try:
            # Find the transaction
            reference = data.get('reference')
            if not reference:
                _logger.warning("Geidea webhook: No reference found in data")
                return werkzeug.Response(status=400)

            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference),
                ('provider_code', '=', 'geidea')
            ])
            
            if not tx_sudo:
                _logger.warning("Geidea webhook: No transaction found for reference %s", reference)
                return werkzeug.Response(status=404)

            # Process the notification
            tx_sudo._process_notification_data(data)
            
            return werkzeug.Response(status=200)
            
        except Exception as e:
            _logger.exception("Error processing Geidea webhook: %s", e)
            return werkzeug.Response(status=500)

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'])
    def geidea_return(self, **data):
        """Handle return from Geidea payment page."""
        _logger.info("Received Geidea return with data: %s", data)
        
        try:
            # Find the transaction
            reference = data.get('reference')
            if not reference:
                _logger.warning("Geidea return: No reference found in data")
                return request.redirect('/payment/status')

            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference),
                ('provider_code', '=', 'geidea')
            ])
            
            if not tx_sudo:
                _logger.warning("Geidea return: No transaction found for reference %s", reference)
                return request.redirect('/payment/status')

            # Process the notification (if not already processed by webhook)
            if tx_sudo.state == 'draft':
                tx_sudo._process_notification_data(data)
            
            return request.redirect('/payment/status')
            
        except Exception as e:
            _logger.exception("Error processing Geidea return: %s", e)
            return request.redirect('/payment/status')

    @http.route('/payment/geidea/payment', type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_payment(self, **data):
        """Handle payment form submission."""
        _logger.info("Processing Geidea payment with data: %s", data)
        
        try:
            # This would typically redirect to Geidea's payment page
            # For now, we'll just simulate a successful payment
            reference = data.get('reference')
            
            # In a real implementation, you would:
            # 1. Validate the payment data
            # 2. Send request to Geidea API
            # 3. Redirect to Geidea payment page
            # 4. Handle the response
            
            # For this demo, redirect back with success
            return request.redirect(f'/payment/geidea/return?reference={reference}&status=success')
            
        except Exception as e:
            _logger.exception("Error processing Geidea payment: %s", e)
            return request.redirect('/payment/status')