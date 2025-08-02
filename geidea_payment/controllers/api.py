# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)


class GeideaApiController(http.Controller):

    @http.route('/geidea/api/payment', type='json', auth='user', methods=['POST'])
    def process_payment(self, **kwargs):
        """API endpoint for processing Geidea payments"""
        try:
            data = kwargs
            provider_id = data.get('provider_id')
            amount = data.get('amount')
            currency_id = data.get('currency_id')
            
            if not all([provider_id, amount, currency_id]):
                return {'error': 'Missing required parameters'}
            
            # Get the provider
            provider = request.env['payment.provider'].browse(provider_id)
            if provider.code != 'geidea':
                return {'error': 'Invalid provider'}
            
            # Create transaction
            transaction = request.env['geidea.transaction'].create({
                'provider_id': provider_id,
                'amount': amount,
                'currency_id': currency_id,
                'state': 'pending'
            })
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'geidea_transaction_id': transaction.transaction_id
            }
            
        except Exception as e:
            _logger.error('Error in payment API: %s', str(e))
            return {'error': str(e)}

    @http.route('/geidea/api/device', type='json', auth='user', methods=['GET', 'POST'])
    def manage_device(self, **kwargs):
        """API endpoint for device management"""
        try:
            method = kwargs.get('method', 'list')
            
            if method == 'list':
                devices = request.env['geidea.device'].search([])
                return {
                    'devices': [{
                        'id': d.id,
                        'name': d.name,
                        'device_id': d.device_id,
                        'device_type': d.device_type,
                        'platform': d.platform,
                        'status': d.status,
                        'last_connection': d.last_connection.isoformat() if d.last_connection else None
                    } for d in devices]
                }
            
            elif method == 'register':
                device_data = kwargs.get('device_data', {})
                required_fields = ['name', 'device_id', 'device_type', 'platform', 'connection_type', 'provider_id']
                
                if not all(field in device_data for field in required_fields):
                    return {'error': 'Missing required device data'}
                
                device = request.env['geidea.device'].create(device_data)
                return {
                    'success': True,
                    'device_id': device.id,
                    'message': 'Device registered successfully'
                }
            
            elif method == 'update_status':
                device_id = kwargs.get('device_id')
                status = kwargs.get('status')
                
                if not device_id or not status:
                    return {'error': 'Device ID and status required'}
                
                device = request.env['geidea.device'].browse(device_id)
                device.write({
                    'status': status,
                    'last_connection': request.env.cr.now() if status == 'connected' else device.last_connection
                })
                
                return {'success': True, 'message': 'Device status updated'}
            
            else:
                return {'error': 'Invalid method'}
                
        except Exception as e:
            _logger.error('Error in device API: %s', str(e))
            return {'error': str(e)}

    @http.route('/geidea/api/transaction/status', type='json', auth='user', methods=['POST'])
    def get_transaction_status(self, **kwargs):
        """Get transaction status"""
        try:
            transaction_id = kwargs.get('transaction_id')
            geidea_transaction_id = kwargs.get('geidea_transaction_id')
            
            domain = []
            if transaction_id:
                domain.append(('id', '=', transaction_id))
            elif geidea_transaction_id:
                domain.append(('transaction_id', '=', geidea_transaction_id))
            else:
                return {'error': 'Transaction ID required'}
            
            transaction = request.env['geidea.transaction'].search(domain, limit=1)
            if not transaction:
                return {'error': 'Transaction not found'}
            
            return {
                'transaction_id': transaction.id,
                'geidea_transaction_id': transaction.transaction_id,
                'state': transaction.state,
                'amount': transaction.amount,
                'currency': transaction.currency_id.name,
                'response_code': transaction.response_code,
                'response_message': transaction.response_message,
                'processed_date': transaction.processed_date.isoformat() if transaction.processed_date else None
            }
            
        except Exception as e:
            _logger.error('Error getting transaction status: %s', str(e))
            return {'error': str(e)}