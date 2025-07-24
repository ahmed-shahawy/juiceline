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