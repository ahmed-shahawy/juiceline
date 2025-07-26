# -*- coding: utf-8 -*-

import json
import logging
import pprint

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaPaymentController(http.Controller):

    @http.route('/payment/geidea/webhook', type='http', auth='public', methods=['POST'], csrf=False, save_session=False)
    def geidea_webhook(self, **post):
        """Handle Geidea webhook notifications"""
        _logger.info("Received Geidea webhook with data:\n%s", pprint.pformat(post))
        
        try:
            # Validate webhook signature if configured
            provider = request.env['payment.provider'].sudo().search([('code', '=', 'geidea')], limit=1)
            if provider and provider.geidea_webhook_secret:
                self._verify_webhook_signature(provider, request.httprequest)
            
            # Process the notification
            request.env['payment.transaction'].sudo()._handle_notification_data('geidea', post)
            
        except Exception as e:
            _logger.error("Error processing Geidea webhook: %s", str(e))
            return request.make_response("Error", status=400)
            
        return request.make_response("OK", status=200)

    @http.route('/payment/geidea/return', type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def geidea_return(self, **post):
        """Handle return from Geidea payment page"""
        _logger.info("Handling Geidea return with data:\n%s", pprint.pformat(post))
        
        try:
            # Process the return data
            request.env['payment.transaction'].sudo()._handle_notification_data('geidea', post)
            
        except Exception as e:
            _logger.error("Error processing Geidea return: %s", str(e))
            
        # Redirect to payment status page
        return request.redirect('/payment/status')

    def _verify_webhook_signature(self, provider, http_request):
        """Verify webhook signature for security"""
        signature = http_request.headers.get('X-Geidea-Signature')
        if not signature:
            raise ValidationError("Missing webhook signature")
            
        # Implement signature verification logic here
        # This is a placeholder - actual implementation would depend on Geidea's specification
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            provider.geidea_webhook_secret.encode('utf-8'),
            http_request.data,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise ValidationError("Invalid webhook signature")

    @http.route('/payment/geidea/pos/process', type='json', auth='user', methods=['POST'])
    def process_pos_payment(self, **post):
        """Process POS payment through Geidea"""
        try:
            amount = post.get('amount')
            currency = post.get('currency')
            reference = post.get('reference')
            pos_config_id = post.get('pos_config_id')
            
            if not all([amount, currency, reference, pos_config_id]):
                return {'success': False, 'error': 'Missing required parameters'}
            
            # Get POS configuration
            pos_config = request.env['pos.config'].browse(pos_config_id)
            if not pos_config.exists():
                return {'success': False, 'error': 'Invalid POS configuration'}
            
            # Create payment transaction
            transaction_data = {
                'amount': amount,
                'currency_id': request.env['res.currency'].search([('name', '=', currency)]).id,
                'reference': reference,
                'provider_code': 'geidea',
                'operation': 'online_direct',
            }
            
            # Find or create Geidea payment provider
            provider = request.env['payment.provider'].search([('code', '=', 'geidea')], limit=1)
            if not provider:
                return {'success': False, 'error': 'Geidea payment provider not configured'}
            
            transaction_data['provider_id'] = provider.id
            
            # Create transaction
            transaction = request.env['payment.transaction'].create(transaction_data)
            
            # Process payment
            result = transaction._send_payment_request()
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'redirect_url': result,
                'geidea_transaction_id': transaction.geidea_transaction_id,
            }
            
        except Exception as e:
            _logger.error("POS payment processing error: %s", str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/payment/geidea/pos/status', type='json', auth='user', methods=['POST'])
    def get_pos_payment_status(self, **post):
        """Get POS payment status"""
        try:
            transaction_id = post.get('transaction_id')
            if not transaction_id:
                return {'success': False, 'error': 'Missing transaction ID'}
            
            transaction = request.env['payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                return {'success': False, 'error': 'Transaction not found'}
            
            return {
                'success': True,
                'state': transaction.state,
                'geidea_transaction_id': transaction.geidea_transaction_id,
                'response_message': transaction.geidea_response_message,
                'amount': transaction.amount,
                'currency': transaction.currency_id.name,
            }
            
        except Exception as e:
            _logger.error("Error getting payment status: %s", str(e))
            return {'success': False, 'error': str(e)}