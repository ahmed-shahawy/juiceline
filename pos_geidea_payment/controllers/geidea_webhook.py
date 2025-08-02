# -*- coding: utf-8 -*-

import json
import logging
import hmac
import hashlib
from werkzeug.exceptions import BadRequest

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaWebhookController(http.Controller):
    """Controller for handling Geidea webhooks"""

    @http.route('/geidea/webhook/payment', type='http', auth='none', methods=['POST'], csrf=False)
    def handle_payment_webhook(self, **kwargs):
        """Handle payment webhook from Geidea"""
        try:
            # Get request data
            data = request.httprequest.get_data()
            
            if not data:
                _logger.error('Empty webhook data received')
                return 'Bad Request', 400
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                _logger.error('Invalid JSON in webhook data')
                return 'Bad Request', 400
            
            # Validate webhook signature
            if not self._validate_webhook_signature(data, request.httprequest.headers):
                _logger.error('Invalid webhook signature')
                return 'Unauthorized', 401
            
            # Process webhook data
            self._process_payment_webhook(webhook_data)
            
            return 'OK', 200
            
        except Exception as e:
            _logger.error('Error processing payment webhook: %s', str(e))
            return 'Internal Server Error', 500

    @http.route('/geidea/webhook/device', type='http', auth='none', methods=['POST'], csrf=False)
    def handle_device_webhook(self, **kwargs):
        """Handle device status webhook from Geidea"""
        try:
            # Get request data
            data = request.httprequest.get_data()
            
            if not data:
                _logger.error('Empty webhook data received')
                return 'Bad Request', 400
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                _logger.error('Invalid JSON in webhook data')
                return 'Bad Request', 400
            
            # Validate webhook signature
            if not self._validate_webhook_signature(data, request.httprequest.headers):
                _logger.error('Invalid webhook signature')
                return 'Unauthorized', 401
            
            # Process webhook data
            self._process_device_webhook(webhook_data)
            
            return 'OK', 200
            
        except Exception as e:
            _logger.error('Error processing device webhook: %s', str(e))
            return 'Internal Server Error', 500

    def _validate_webhook_signature(self, data, headers):
        """Validate webhook signature"""
        try:
            # Get signature from headers
            signature = headers.get('X-Geidea-Signature') or headers.get('x-geidea-signature')
            if not signature:
                _logger.warning('No signature found in webhook headers')
                return False
            
            # Get merchant ID to find configuration
            webhook_data = json.loads(data.decode('utf-8'))
            merchant_id = webhook_data.get('merchant_id')
            
            if not merchant_id:
                _logger.warning('No merchant_id found in webhook data')
                return False
            
            # Find configuration
            config = request.env['geidea.config'].sudo().search([
                ('merchant_id', '=', merchant_id),
                ('active', '=', True)
            ], limit=1)
            
            if not config or not config.webhook_secret:
                _logger.warning('No valid configuration found for merchant_id: %s', merchant_id)
                return False
            
            # Calculate expected signature
            expected_signature = hmac.new(
                config.webhook_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            _logger.error('Error validating webhook signature: %s', str(e))
            return False

    def _process_payment_webhook(self, webhook_data):
        """Process payment webhook data"""
        try:
            # Extract transaction information
            transaction_id = webhook_data.get('transaction_id')
            status = webhook_data.get('status')
            merchant_id = webhook_data.get('merchant_id')
            
            if not all([transaction_id, status, merchant_id]):
                _logger.error('Missing required fields in payment webhook')
                return
            
            # Find the transaction
            transaction = request.env['geidea.transaction'].sudo().search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
            
            if not transaction:
                _logger.warning('Transaction not found: %s', transaction_id)
                return
            
            # Update transaction based on webhook status
            status_mapping = {
                'completed': 'completed',
                'failed': 'failed',
                'cancelled': 'cancelled',
                'refunded': 'refunded',
                'processing': 'processing',
            }
            
            new_state = status_mapping.get(status.lower())
            if new_state and new_state != transaction.state:
                transaction.write({
                    'state': new_state,
                    'response_code': webhook_data.get('response_code'),
                    'response_message': webhook_data.get('response_message'),
                    'authorization_code': webhook_data.get('authorization_code'),
                    'gateway_transaction_id': webhook_data.get('gateway_transaction_id'),
                    'rrn': webhook_data.get('rrn'),
                    'raw_response': json.dumps(webhook_data),
                })
                
                if new_state == 'completed':
                    transaction.completed_at = request.env.cr.now()
                elif new_state == 'failed':
                    transaction.write({
                        'error_code': webhook_data.get('error_code'),
                        'error_message': webhook_data.get('error_message'),
                    })
            
            _logger.info('Processed payment webhook for transaction: %s, status: %s', 
                        transaction_id, status)
            
        except Exception as e:
            _logger.error('Error processing payment webhook: %s', str(e))
            raise

    def _process_device_webhook(self, webhook_data):
        """Process device webhook data"""
        try:
            # Extract device information
            device_id = webhook_data.get('device_id')
            status = webhook_data.get('status')
            merchant_id = webhook_data.get('merchant_id')
            
            if not all([device_id, status, merchant_id]):
                _logger.error('Missing required fields in device webhook')
                return
            
            # Find the device
            device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', device_id),
                ('config_id.merchant_id', '=', merchant_id)
            ], limit=1)
            
            if not device:
                _logger.warning('Device not found: %s', device_id)
                return
            
            # Update device status
            status_mapping = {
                'online': 'online',
                'offline': 'offline',
                'busy': 'busy',
                'error': 'error',
                'maintenance': 'maintenance',
            }
            
            new_status = status_mapping.get(status.lower())
            if new_status:
                device.write({
                    'status': new_status,
                    'last_seen': request.env.cr.now(),
                })
                
                if new_status == 'error':
                    device.write({
                        'error_message': webhook_data.get('error_message'),
                        'error_count': device.error_count + 1,
                    })
                elif new_status == 'online':
                    device.write({
                        'error_message': False,
                        'error_count': 0,
                    })
            
            _logger.info('Processed device webhook for device: %s, status: %s', 
                        device_id, status)
            
        except Exception as e:
            _logger.error('Error processing device webhook: %s', str(e))
            raise

    @http.route('/geidea/webhook/test', type='http', auth='user', methods=['GET'])
    def test_webhook_endpoint(self, **kwargs):
        """Test webhook endpoint accessibility"""
        return json.dumps({
            'status': 'ok',
            'message': 'Webhook endpoint is accessible',
            'timestamp': request.env.cr.now().isoformat(),
        })