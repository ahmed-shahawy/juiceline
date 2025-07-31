# -*- coding: utf-8 -*-

import json
import logging
import pprint
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):
    """
    Controller for handling Geidea payment gateway interactions.
    Implements improved REST API responses with JSON format (REST API fix #4).
    """
    
    _return_url = '/payment/geidea/return'
    _webhook_url = '/payment/geidea/webhook'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def geidea_return_from_checkout(self, **data):
        """Handle return from Geidea checkout page."""
        _logger.info('Geidea return data:\n%s', pprint.pformat(data))
        
        try:
            # Process the return data
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'geidea', data
            )
            tx_sudo._process_notification_data(data)
            tx_sudo._execute_callback()
            
            # Redirect to the appropriate page
            return request.redirect('/payment/status')
            
        except ValidationError as e:
            _logger.exception('Geidea return validation error: %s', str(e))
            return request.redirect('/payment/status?error=validation')
        except Exception as e:
            _logger.exception('Geidea return processing error: %s', str(e))
            return request.redirect('/payment/status?error=processing')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_webhook(self, **data):
        """
        Handle Geidea webhook notifications.
        Returns JSON responses instead of plain text (REST API fix #4).
        """
        _logger.info('Geidea webhook data:\n%s', pprint.pformat(data))
        
        try:
            # Verify webhook authenticity (implement signature verification)
            if not self._verify_webhook_signature(data):
                _logger.warning('Geidea webhook signature verification failed')
                return self._json_response({'error': 'Invalid signature'}, status=403)
            
            # Process the webhook data
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'geidea', data
            )
            tx_sudo._process_notification_data(data)
            tx_sudo._execute_callback()
            
            # Return JSON success response
            return self._json_response({
                'status': 'success',
                'message': 'Webhook processed successfully',
                'transaction_id': tx_sudo.geidea_transaction_id
            })
            
        except ValidationError as e:
            _logger.exception('Geidea webhook validation error: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': f'Validation error: {str(e)}'
            }, status=400)
        except Exception as e:
            _logger.exception('Geidea webhook processing error: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': f'Processing error: {str(e)}'
            }, status=500)

    @http.route('/payment/geidea/checkout', type='json', auth='public', methods=['POST'])
    def geidea_checkout(self, **kwargs):
        """
        Handle Geidea checkout initialization.
        Returns JSON responses for better error handling (REST API fix #4).
        """
        try:
            # Extract and validate checkout data
            tx_id = kwargs.get('tx_id')
            if not tx_id:
                return self._json_error('Missing transaction ID', 400)
            
            tx_sudo = request.env['payment.transaction'].sudo().browse(tx_id)
            if not tx_sudo.exists():
                return self._json_error('Transaction not found', 404)
            
            if tx_sudo.provider_code != 'geidea':
                return self._json_error('Invalid payment provider', 400)
            
            # Generate checkout URL and parameters
            checkout_data = self._prepare_checkout_data(tx_sudo)
            
            return {
                'status': 'success',
                'data': checkout_data
            }
            
        except Exception as e:
            _logger.exception('Geidea checkout error: %s', str(e))
            return self._json_error(f'Checkout error: {str(e)}', 500)

    @http.route('/api/geidea/transaction/status', type='json', auth='user', methods=['POST'])
    def get_transaction_status(self, **kwargs):
        """
        Get transaction status via API.
        Provides JSON-formatted responses (REST API fix #4).
        """
        try:
            reference = kwargs.get('reference')
            geidea_tx_id = kwargs.get('geidea_transaction_id')
            
            if not reference and not geidea_tx_id:
                return self._json_error('Missing transaction reference or Geidea transaction ID', 400)
            
            # Find transaction
            domain = [('provider_code', '=', 'geidea')]
            if reference:
                domain.append(('reference', '=', reference))
            elif geidea_tx_id:
                domain.append(('geidea_transaction_id', '=', geidea_tx_id))
            
            tx = request.env['payment.transaction'].search(domain, limit=1)
            if not tx:
                return self._json_error('Transaction not found', 404)
            
            # Return transaction status
            return {
                'status': 'success',
                'data': {
                    'reference': tx.reference,
                    'state': tx.state,
                    'geidea_transaction_id': tx.geidea_transaction_id,
                    'geidea_response_code': tx.geidea_response_code,
                    'geidea_response_message': tx.geidea_response_message,
                    'amount': tx.amount,
                    'currency': tx.currency_id.name,
                    'processed_at': tx.geidea_processed_at.isoformat() if tx.geidea_processed_at else None,
                }
            }
            
        except Exception as e:
            _logger.exception('Transaction status error: %s', str(e))
            return self._json_error(f'Status check error: {str(e)}', 500)

    @http.route('/api/geidea/refund', type='json', auth='user', methods=['POST'])
    def process_refund(self, **kwargs):
        """
        Process refund via API.
        Returns structured JSON responses (REST API fix #4).
        """
        try:
            tx_id = kwargs.get('tx_id')
            amount = kwargs.get('amount')
            
            if not tx_id:
                return self._json_error('Missing transaction ID', 400)
            
            tx = request.env['payment.transaction'].browse(tx_id)
            if not tx.exists():
                return self._json_error('Transaction not found', 404)
            
            if tx.provider_code != 'geidea':
                return self._json_error('Invalid payment provider', 400)
            
            if tx.state != 'done':
                return self._json_error('Transaction must be completed to process refund', 400)
            
            # Validate refund amount
            if amount and amount > tx.amount:
                return self._json_error('Refund amount cannot exceed transaction amount', 400)
            
            # Process refund asynchronously
            tx._geidea_refund_transaction(amount)
            
            return {
                'status': 'success',
                'message': 'Refund request submitted successfully',
                'data': {
                    'transaction_id': tx.reference,
                    'refund_amount': amount or tx.amount,
                }
            }
            
        except Exception as e:
            _logger.exception('Refund processing error: %s', str(e))
            return self._json_error(f'Refund error: {str(e)}', 500)

    def _verify_webhook_signature(self, data):
        """
        Verify webhook signature for security.
        This is a placeholder - implement actual signature verification based on Geidea's requirements.
        
        Args:
            data (dict): Webhook data
            
        Returns:
            bool: True if signature is valid
        """
        # TODO: Implement actual signature verification
        # For now, return True to allow processing
        return True

    def _prepare_checkout_data(self, tx_sudo):
        """
        Prepare checkout data for Geidea payment.
        
        Args:
            tx_sudo: Payment transaction record
            
        Returns:
            dict: Checkout data
        """
        provider = tx_sudo.provider_id
        
        return {
            'checkout_url': provider._geidea_get_api_url('checkout'),
            'merchant_id': provider.geidea_merchant_id,
            'amount': tx_sudo.amount,
            'currency': tx_sudo.currency_id.name,
            'order_id': tx_sudo.geidea_order_id or tx_sudo.reference,
            'customer_email': tx_sudo.partner_email or '',
            'return_url': request.httprequest.url_root.rstrip('/') + self._return_url,
            'callback_url': request.httprequest.url_root.rstrip('/') + self._webhook_url,
        }

    def _json_response(self, data, status=200):
        """
        Create JSON response with proper headers.
        Implements improved JSON responses (REST API fix #4).
        
        Args:
            data (dict): Response data
            status (int): HTTP status code
            
        Returns:
            werkzeug.Response: JSON response
        """
        response = request.make_response(
            json.dumps(data),
            headers=[
                ('Content-Type', 'application/json'),
                ('Cache-Control', 'no-cache'),
            ]
        )
        response.status_code = status
        return response

    def _json_error(self, message, status=400):
        """
        Create JSON error response.
        
        Args:
            message (str): Error message
            status (int): HTTP status code
            
        Returns:
            dict: Error response data
        """
        return {
            'status': 'error',
            'message': message,
            'error_code': status
        }