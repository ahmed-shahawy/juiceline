# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaPaymentController(http.Controller):

    @http.route('/geidea/api/payment', type='json', auth='user', methods=['POST'])
    def process_payment(self, **kwargs):
        """Process payment through Geidea gateway"""
        try:
            amount = kwargs.get('amount')
            device_id = kwargs.get('device_id')
            payment_method = kwargs.get('payment_method', 'card')
            
            if not amount or not device_id:
                return {'error': 'Missing required parameters'}
            
            # Get device and acquirer
            device = request.env['geidea.device'].browse(int(device_id))
            if not device.exists():
                return {'error': 'Invalid device ID'}
            
            # Create transaction
            transaction = request.env['geidea.transaction'].create({
                'amount': float(amount),
                'payment_method': payment_method,
                'device_id': device.id,
                'acquirer_id': device.acquirer_id.id,
                'state': 'draft'
            })
            
            # Process payment
            result = transaction.process_payment()
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'transaction_ref': transaction.name,
                'state': transaction.state
            }
            
        except Exception as e:
            _logger.error(f"Payment processing error: {str(e)}")
            return {'error': str(e)}

    @http.route('/geidea/api/device/status', type='json', auth='user', methods=['GET'])
    def get_device_status(self, device_id=None):
        """Get device connection status"""
        try:
            if device_id:
                device = request.env['geidea.device'].browse(int(device_id))
                if device.exists():
                    return {
                        'device_id': device.id,
                        'status': device.connection_status,
                        'last_connected': device.last_connected.isoformat() if device.last_connected else None
                    }
                else:
                    return {'error': 'Device not found'}
            else:
                devices = request.env['geidea.device'].search([('active', '=', True)])
                return [{
                    'device_id': device.id,
                    'name': device.name,
                    'status': device.connection_status,
                    'last_connected': device.last_connected.isoformat() if device.last_connected else None
                } for device in devices]
                
        except Exception as e:
            _logger.error(f"Device status error: {str(e)}")
            return {'error': str(e)}

    @http.route('/geidea/api/device/connect', type='json', auth='user', methods=['POST'])
    def connect_device(self, device_id):
        """Connect to a payment device"""
        try:
            device = request.env['geidea.device'].browse(int(device_id))
            if not device.exists():
                return {'error': 'Device not found'}
            
            success = device.connect_device()
            return {
                'success': success,
                'status': device.connection_status
            }
            
        except Exception as e:
            _logger.error(f"Device connection error: {str(e)}")
            return {'error': str(e)}

    @http.route('/geidea/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def webhook_handler(self, **kwargs):
        """Handle webhooks from Geidea payment gateway"""
        try:
            _logger.info(f"Received Geidea webhook: {kwargs}")
            
            transaction_id = kwargs.get('transaction_id')
            status = kwargs.get('status')
            
            if transaction_id:
                transaction = request.env['geidea.transaction'].sudo().search([
                    ('transaction_id', '=', transaction_id)
                ], limit=1)
                
                if transaction:
                    if status == 'completed':
                        transaction.state = 'captured'
                    elif status == 'failed':
                        transaction.state = 'error'
                        transaction.error_message = kwargs.get('error_message', 'Payment failed')
                    
                    _logger.info(f"Updated transaction {transaction.name} status to {transaction.state}")
            
            return {'status': 'received'}
            
        except Exception as e:
            _logger.error(f"Webhook processing error: {str(e)}")
            return {'error': str(e)}