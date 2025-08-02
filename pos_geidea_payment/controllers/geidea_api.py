# -*- coding: utf-8 -*-

import json
import logging
from werkzeug.exceptions import BadRequest

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class GeideaAPIController(http.Controller):
    """Controller for Geidea payment API endpoints"""

    @http.route('/geidea/api/payment/process', type='json', auth='user', methods=['POST'])
    def process_payment(self, **kwargs):
        """Process a payment through Geidea"""
        try:
            # Extract payment data
            payment_data = kwargs.get('payment_data', {})
            config_id = payment_data.get('config_id')
            device_id = payment_data.get('device_id')
            amount = payment_data.get('amount')
            currency_id = payment_data.get('currency_id')
            
            # Validate required fields
            if not all([config_id, amount, currency_id]):
                raise ValidationError(_('Missing required payment data'))
            
            # Get configuration
            config = request.env['geidea.config'].browse(config_id)
            if not config.exists():
                raise ValidationError(_('Invalid Geidea configuration'))
            
            # Create transaction
            transaction_vals = {
                'transaction_id': 'TXN_%s' % request.env['ir.sequence'].next_by_code('geidea.transaction'),
                'config_id': config_id,
                'device_id': device_id,
                'amount': amount,
                'currency_id': currency_id,
                'type': payment_data.get('type', 'sale'),
                'reference': payment_data.get('reference'),
                'order_id': payment_data.get('order_id'),
                'payment_method': payment_data.get('payment_method'),
                'customer_email': payment_data.get('customer_email'),
                'customer_phone': payment_data.get('customer_phone'),
                'metadata': json.dumps(payment_data.get('metadata', {})),
            }
            
            transaction = request.env['geidea.transaction'].create(transaction_vals)
            
            # Process the transaction
            transaction.action_process()
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'state': transaction.state,
                'message': _('Payment processed successfully'),
                'receipt_data': transaction.get_receipt_data(),
            }
            
        except Exception as e:
            _logger.error('Geidea payment processing error: %s', str(e))
            return {
                'success': False,
                'error': str(e),
                'message': _('Payment processing failed'),
            }

    @http.route('/geidea/api/payment/status/<string:transaction_id>', type='json', auth='user', methods=['GET'])
    def get_payment_status(self, transaction_id, **kwargs):
        """Get payment status by transaction ID"""
        try:
            transaction = request.env['geidea.transaction'].search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
            
            if not transaction:
                raise ValidationError(_('Transaction not found'))
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'state': transaction.state,
                'amount': transaction.amount,
                'currency': transaction.currency_id.name,
                'processed_at': transaction.processed_at,
                'authorization_code': transaction.authorization_code,
                'response_message': transaction.response_message,
            }
            
        except Exception as e:
            _logger.error('Error getting payment status: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route('/geidea/api/payment/refund', type='json', auth='user', methods=['POST'])
    def refund_payment(self, **kwargs):
        """Refund a payment"""
        try:
            refund_data = kwargs.get('refund_data', {})
            transaction_id = refund_data.get('transaction_id')
            refund_amount = refund_data.get('amount')
            
            if not transaction_id:
                raise ValidationError(_('Transaction ID is required'))
            
            transaction = request.env['geidea.transaction'].search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
            
            if not transaction:
                raise ValidationError(_('Transaction not found'))
            
            # Process refund
            transaction.action_refund(refund_amount)
            
            return {
                'success': True,
                'message': _('Refund processed successfully'),
                'refund_amount': refund_amount or transaction.remaining_amount,
            }
            
        except Exception as e:
            _logger.error('Geidea refund processing error: %s', str(e))
            return {
                'success': False,
                'error': str(e),
                'message': _('Refund processing failed'),
            }

    @http.route('/geidea/api/device/status', type='json', auth='user', methods=['GET'])
    def get_device_status(self, **kwargs):
        """Get status of all registered devices"""
        try:
            company_id = request.env.company.id
            devices = request.env['geidea.device'].search([
                ('config_id.company_id', '=', company_id),
                ('active', '=', True)
            ])
            
            device_status = []
            for device in devices:
                device_status.append({
                    'id': device.id,
                    'name': device.name,
                    'device_id': device.device_id,
                    'platform': device.platform,
                    'status': device.status,
                    'last_seen': device.last_seen,
                    'ip_address': device.ip_address,
                    'connection_type': device.connection_type,
                })
            
            return {
                'success': True,
                'devices': device_status,
            }
            
        except Exception as e:
            _logger.error('Error getting device status: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route('/geidea/api/device/test/<int:device_id>', type='json', auth='user', methods=['POST'])
    def test_device_connection(self, device_id, **kwargs):
        """Test connection to a specific device"""
        try:
            device = request.env['geidea.device'].browse(device_id)
            if not device.exists():
                raise ValidationError(_('Device not found'))
            
            result = device.test_connection()
            
            return {
                'success': True,
                'device_id': device.id,
                'status': device.status,
                'message': _('Device connection test completed'),
            }
            
        except Exception as e:
            _logger.error('Error testing device connection: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route('/geidea/api/config/test/<int:config_id>', type='json', auth='user', methods=['POST'])
    def test_configuration(self, config_id, **kwargs):
        """Test Geidea configuration"""
        try:
            config = request.env['geidea.config'].browse(config_id)
            if not config.exists():
                raise ValidationError(_('Configuration not found'))
            
            result = config.test_connection()
            
            return {
                'success': True,
                'config_id': config.id,
                'connection_status': config.connection_status,
                'message': _('Configuration test completed'),
            }
            
        except Exception as e:
            _logger.error('Error testing configuration: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route('/geidea/api/transactions', type='json', auth='user', methods=['GET'])
    def get_transactions(self, **kwargs):
        """Get transaction history"""
        try:
            domain = []
            
            # Filter by date range if provided
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            
            # Filter by state if provided
            state = kwargs.get('state')
            if state:
                domain.append(('state', '=', state))
            
            # Filter by company
            company_id = request.env.company.id
            domain.append(('config_id.company_id', '=', company_id))
            
            # Get transactions
            limit = kwargs.get('limit', 100)
            transactions = request.env['geidea.transaction'].search(
                domain, limit=limit, order='create_date desc'
            )
            
            transaction_data = []
            for transaction in transactions:
                transaction_data.append({
                    'id': transaction.id,
                    'transaction_id': transaction.transaction_id,
                    'amount': transaction.amount,
                    'currency': transaction.currency_id.name,
                    'state': transaction.state,
                    'type': transaction.type,
                    'payment_method': transaction.payment_method,
                    'card_last_four': transaction.card_last_four,
                    'created_at': transaction.create_date,
                    'processed_at': transaction.processed_at,
                    'device_name': transaction.device_id.name if transaction.device_id else None,
                })
            
            return {
                'success': True,
                'transactions': transaction_data,
                'count': len(transaction_data),
            }
            
        except Exception as e:
            _logger.error('Error getting transactions: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }