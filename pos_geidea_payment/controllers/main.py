from odoo import http, _
from odoo.http import request
import json
import logging
import requests
from datetime import datetime
from werkzeug.exceptions import BadRequest

_logger = logging.getLogger(__name__)

class GeideaController(http.Controller):
    
    @http.route('/pos_geidea/process_payment', type='json', auth='user')
    def process_payment(self, **post):
        try:
            # Validate request data
            data = json.loads(request.httprequest.data)
            self._validate_payment_data(data)
            
            # Get terminal configuration
            terminal = self._get_terminal(data['terminal_id'])
            if not terminal:
                return {'success': False, 'error': _('Terminal not found')}
            
            # Create transaction record
            transaction = self._create_transaction(terminal, data)
            
            # Process payment through Geidea API
            payment_result = self._process_geidea_payment(terminal, transaction)
            
            # Update transaction record
            self._update_transaction(transaction, payment_result)
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'reference': transaction.name,
                'status': transaction.state,
            }
            
        except Exception as e:
            _logger.error("Geidea payment processing error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/pos_geidea/cancel_payment', type='json', auth='user')
    def cancel_payment(self, **post):
        try:
            data = json.loads(request.httprequest.data)
            transaction = request.env['geidea.transaction'].sudo().search([
                ('pos_order_ref', '=', data['order_ref']),
                ('state', 'in', ['pending', 'completed'])
            ], limit=1)
            
            if not transaction:
                return {'success': False, 'error': _('Transaction not found')}
            
            cancel_result = self._cancel_geidea_payment(transaction)
            
            transaction.write({
                'state': 'cancelled',
                'response_message': 'Payment cancelled'
            })
            
            return {'success': True}
            
        except Exception as e:
            _logger.error("Geidea payment cancellation error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def _validate_payment_data(self, data):
        required_fields = ['amount', 'currency', 'terminal_id', 'merchant_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise BadRequest(_('Missing required fields: %s') % ', '.join(missing_fields))
        
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            raise BadRequest(_('Invalid amount'))
    
    def _get_terminal(self, terminal_id):
        return request.env['geidea.terminal'].sudo().search([
            ('terminal_id', '=', terminal_id),
            ('state', '=', 'active')
        ], limit=1)
    
    def _create_transaction(self, terminal, data):
        return request.env['geidea.transaction'].sudo().create({
            'terminal_id': terminal.id,
            'amount': data['amount'],
            'currency_id': request.env['res.currency'].search([
                ('name', '=', data['currency'])
            ], limit=1).id,
            'pos_order_ref': data.get('order_ref'),
            'customer_email': data.get('customer', {}).get('email'),
            'customer_phone': data.get('customer', {}).get('phone'),
            'is_test_mode': data.get('test_mode', False),
            'state': 'pending'
        })
    
    def _process_geidea_payment(self, terminal, transaction):
        headers = {
            'Authorization': f"Bearer {terminal._decrypt_sensitive_data(terminal.api_key)}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'amount': transaction.amount,
            'currency': transaction.currency_id.name,
            'merchantId': terminal.merchant_id,
            'terminalId': terminal.terminal_id,
            'orderId': transaction.name,
            'customerEmail': transaction.customer_email,
            'customerPhone': transaction.customer_phone,
            'isTest': transaction.is_test_mode,
        }
        
        try:
            response = requests.post(
                f"{self._get_api_url()}/payment/process",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.error("Geidea API error: %s", str(e))
            raise
    
    def _cancel_geidea_payment(self, transaction):
        terminal = transaction.terminal_id
        headers = {
            'Authorization': f"Bearer {terminal._decrypt_sensitive_data(terminal.api_key)}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'transactionId': transaction.geidea_reference,
            'merchantId': terminal.merchant_id,
            'terminalId': terminal.terminal_id,
        }
        
        try:
            response = requests.post(
                f"{self._get_api_url()}/payment/cancel",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.error("Geidea API error: %s", str(e))
            raise
    
    def _update_transaction(self, transaction, result):
        transaction.write({
            'state': 'completed' if result.get('success') else 'failed',
            'geidea_reference': result.get('reference'),
            'approval_code': result.get('approvalCode'),
            'response_code': result.get('responseCode'),
            'response_message': result.get('message'),
            'card_type': result.get('cardType'),
            'card_number': result.get('cardNumber'),
        })
    
    def _get_api_url(self):
        return request.env['ir.config_parameter'].sudo().get_param(
            'geidea.api_url', 'https://api.geidea.net/v1'
        )
    
    @http.route('/geidea/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def webhook_handler(self, **post):
        """Handle Geidea webhook notifications"""
        try:
            # Verify webhook signature
            signature = request.httprequest.headers.get('X-Geidea-Signature')
            if not self._verify_webhook_signature(signature, request.httprequest.data):
                return {'error': 'Invalid signature'}, 401
            
            data = json.loads(request.httprequest.data)
            event_type = data.get('event_type')
            transaction_data = data.get('transaction', {})
            
            _logger.info("Webhook received - Event: %s, Transaction: %s", 
                        event_type, transaction_data.get('id'))
            
            # Process webhook based on event type
            if event_type == 'payment.completed':
                self._handle_payment_completed(transaction_data)
            elif event_type == 'payment.failed':
                self._handle_payment_failed(transaction_data)
            elif event_type == 'payment.refunded':
                self._handle_payment_refunded(transaction_data)
            elif event_type == 'payment.cancelled':
                self._handle_payment_cancelled(transaction_data)
            else:
                _logger.warning("Unknown webhook event type: %s", event_type)
            
            return {'status': 'received'}
            
        except Exception as e:
            _logger.error("Webhook processing error: %s", str(e))
            return {'error': str(e)}, 500
    
    def _verify_webhook_signature(self, signature, payload):
        """Verify webhook signature for security"""
        if not signature:
            return False
        
        import hmac
        import hashlib
        
        webhook_secret = request.env['ir.config_parameter'].sudo().get_param('geidea.webhook_secret')
        if not webhook_secret:
            _logger.warning("Webhook secret not configured")
            return False
        
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _handle_payment_completed(self, transaction_data):
        """Handle successful payment webhook"""
        reference = transaction_data.get('orderId')
        if not reference:
            return
        
        transaction = request.env['geidea.transaction'].sudo().search([
            ('name', '=', reference),
            ('state', 'in', ['pending', 'draft'])
        ], limit=1)
        
        if transaction:
            transaction.write({
                'state': 'completed',
                'geidea_reference': transaction_data.get('id'),
                'approval_code': transaction_data.get('approvalCode'),
                'response_code': transaction_data.get('responseCode'),
                'response_message': transaction_data.get('responseMessage'),
                'card_type': transaction_data.get('cardType'),
                'card_number': transaction_data.get('maskedCardNumber'),
            })
            transaction._notify_success()
    
    def _handle_payment_failed(self, transaction_data):
        """Handle failed payment webhook"""
        reference = transaction_data.get('orderId')
        if not reference:
            return
        
        transaction = request.env['geidea.transaction'].sudo().search([
            ('name', '=', reference),
            ('state', 'in', ['pending', 'draft'])
        ], limit=1)
        
        if transaction:
            transaction.write({
                'state': 'failed',
                'response_code': transaction_data.get('responseCode'),
                'response_message': transaction_data.get('responseMessage'),
            })
            transaction._notify_failure()
    
    def _handle_payment_refunded(self, transaction_data):
        """Handle refunded payment webhook"""
        reference = transaction_data.get('orderId')
        if not reference:
            return
        
        # Create refund transaction record
        original_transaction = request.env['geidea.transaction'].sudo().search([
            ('geidea_reference', '=', transaction_data.get('originalTransactionId')),
            ('state', '=', 'completed')
        ], limit=1)
        
        if original_transaction:
            refund_transaction = request.env['geidea.transaction'].sudo().create({
                'name': f"REFUND-{reference}",
                'terminal_id': original_transaction.terminal_id.id,
                'amount': transaction_data.get('amount', 0),
                'currency_id': original_transaction.currency_id.id,
                'transaction_type': 'refund',
                'state': 'completed',
                'geidea_reference': transaction_data.get('id'),
                'response_code': transaction_data.get('responseCode'),
                'response_message': transaction_data.get('responseMessage'),
                'pos_order_id': original_transaction.pos_order_id.id,
                'pos_session_id': original_transaction.pos_session_id.id,
            })
    
    def _handle_payment_cancelled(self, transaction_data):
        """Handle cancelled payment webhook"""
        reference = transaction_data.get('orderId')
        if not reference:
            return
        
        transaction = request.env['geidea.transaction'].sudo().search([
            ('name', '=', reference),
            ('state', 'in', ['pending', 'draft'])
        ], limit=1)
        
        if transaction:
            transaction.write({
                'state': 'cancelled',
                'response_message': 'Payment cancelled via webhook'
            })