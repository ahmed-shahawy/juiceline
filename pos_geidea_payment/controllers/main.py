# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class GeideaPaymentController(http.Controller):

    @http.route('/pos/geidea/test_connection', type='json', auth='user')
    def test_geidea_connection(self, **kwargs):
        """Test Geidea payment gateway connection"""
        try:
            # Get current user's company
            company = request.env.user.company_id
            
            # Simulate connection test
            # In a real implementation, this would make an actual API call to Geidea
            result = {
                'success': True,
                'message': _('Connection test successful'),
                'details': {
                    'gateway': 'Geidea Payment Gateway',
                    'status': 'Online',
                    'response_time': '< 100ms',
                    'test_mode': True
                }
            }
            
            return result
            
        except Exception as e:
            _logger.error(f"Geidea connection test failed: {str(e)}")
            return {
                'success': False,
                'message': _('Connection test failed'),
                'error': str(e)
            }

    @http.route('/pos/geidea/process_payment', type='json', auth='user')
    def process_payment(self, **kwargs):
        """Process a payment through Geidea gateway"""
        try:
            payment_data = kwargs
            
            # Validate required fields
            required_fields = ['amount', 'currency', 'order_ref']
            for field in required_fields:
                if field not in payment_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Get POS session
            session_id = payment_data.get('session_id')
            if session_id:
                session = request.env['pos.session'].browse(session_id)
                if not session.exists():
                    raise ValueError("Invalid session ID")
            else:
                # Get current active session
                session = request.env['pos.session'].search([
                    ('state', '=', 'opened'),
                    ('user_id', '=', request.env.user.id)
                ], limit=1)
                if not session:
                    raise ValueError("No active POS session found")
            
            # Create payment record
            payment_vals = {
                'transaction_id': f"GDI_{payment_data['order_ref']}_{request.env['ir.sequence'].next_by_code('geidea.payment') or 'TXN'}",
                'reference': payment_data['order_ref'],
                'pos_session_id': session.id,
                'amount': float(payment_data['amount']),
                'currency_id': request.env['res.currency'].search([('name', '=', payment_data['currency'])], limit=1).id,
                'state': 'pending',
                'payment_method': 'card',
                'device_id': payment_data.get('device_id'),
                'bluetooth_mac': payment_data.get('bluetooth_mac'),
                'ios_device_id': payment_data.get('ios_device_id'),
                'ios_app_state': payment_data.get('ios_app_state'),
                'battery_level': payment_data.get('battery_level'),
                'initiated_at': request.env.cr.now(),
            }
            
            payment = request.env['geidea.payment'].create(payment_vals)
            
            # Simulate payment processing
            # In a real implementation, this would communicate with Geidea API
            import time
            import random
            
            # Simulate processing delay
            processing_time = random.uniform(2, 5)
            time.sleep(processing_time)
            
            # Simulate different outcomes
            success_rate = 0.9  # 90% success rate for simulation
            if random.random() < success_rate:
                # Successful payment
                payment.write({
                    'state': 'completed',
                    'card_type': 'Visa',
                    'last_four_digits': '1234',
                    'geidea_response': json.dumps({
                        'status': 'success',
                        'transaction_id': payment.transaction_id,
                        'auth_code': 'AUTH123456',
                        'response_code': '00',
                        'response_message': 'Approved'
                    }),
                    'completed_at': request.env.cr.now(),
                })
                
                result = {
                    'success': True,
                    'transaction_id': payment.transaction_id,
                    'auth_code': 'AUTH123456',
                    'card_type': 'Visa',
                    'last_four_digits': '1234',
                    'response_code': '00',
                    'amount': payment.amount,
                    'currency': payment_data['currency']
                }
            else:
                # Failed payment
                error_codes = ['05', '14', '51', '54', '61']
                error_messages = [
                    'Do not honor',
                    'Invalid card number',
                    'Insufficient funds',
                    'Expired card',
                    'Exceeds withdrawal limit'
                ]
                
                error_idx = random.randint(0, len(error_codes) - 1)
                error_code = error_codes[error_idx]
                error_message = error_messages[error_idx]
                
                payment.write({
                    'state': 'failed',
                    'error_code': error_code,
                    'error_message': error_message,
                    'geidea_response': json.dumps({
                        'status': 'failed',
                        'error_code': error_code,
                        'error_message': error_message
                    }),
                    'completed_at': request.env.cr.now(),
                })
                
                result = {
                    'success': False,
                    'error_code': error_code,
                    'error_message': error_message,
                    'transaction_id': payment.transaction_id
                }
            
            return result
            
        except Exception as e:
            _logger.error(f"Geidea payment processing failed: {str(e)}")
            return {
                'success': False,
                'error_code': 'SYSTEM_ERROR',
                'error_message': str(e)
            }

    @http.route('/pos/geidea/process_refund', type='json', auth='user')
    def process_refund(self, **kwargs):
        """Process a refund through Geidea gateway"""
        try:
            refund_data = kwargs
            
            # Validate required fields
            original_transaction_id = refund_data.get('original_transaction_id')
            if not original_transaction_id:
                raise ValueError("Original transaction ID is required")
            
            # Find original payment
            original_payment = request.env['geidea.payment'].search([
                ('transaction_id', '=', original_transaction_id),
                ('state', '=', 'completed')
            ], limit=1)
            
            if not original_payment:
                raise ValueError("Original transaction not found or not completed")
            
            refund_amount = float(refund_data.get('amount', original_payment.amount))
            
            # Validate refund amount
            if refund_amount <= 0:
                raise ValueError("Refund amount must be positive")
            
            remaining_amount = original_payment.amount - original_payment.refund_amount
            if refund_amount > remaining_amount:
                raise ValueError("Refund amount exceeds available amount")
            
            # Create refund transaction
            refund_vals = {
                'transaction_id': f"REF_{original_transaction_id}_{len(original_payment.refund_transactions) + 1}",
                'reference': f"Refund for {original_payment.reference}",
                'pos_session_id': original_payment.pos_session_id.id,
                'amount': -refund_amount,
                'currency_id': original_payment.currency_id.id,
                'state': 'pending',
                'payment_method': original_payment.payment_method,
                'original_transaction_id': original_payment.id,
                'device_id': refund_data.get('device_id'),
                'initiated_at': request.env.cr.now(),
            }
            
            refund_payment = request.env['geidea.payment'].create(refund_vals)
            
            # Simulate refund processing
            import time
            import random
            
            time.sleep(random.uniform(1, 3))
            
            # Simulate successful refund (higher success rate)
            if random.random() < 0.95:
                refund_payment.write({
                    'state': 'completed',
                    'geidea_response': json.dumps({
                        'status': 'success',
                        'refund_id': refund_payment.transaction_id,
                        'original_transaction': original_transaction_id,
                        'refund_amount': refund_amount
                    }),
                    'completed_at': request.env.cr.now(),
                })
                
                # Update original payment
                new_refund_amount = original_payment.refund_amount + refund_amount
                if new_refund_amount >= original_payment.amount:
                    original_payment.state = 'refunded'
                else:
                    original_payment.state = 'partially_refunded'
                
                original_payment.refund_amount = new_refund_amount
                
                result = {
                    'success': True,
                    'refund_transaction_id': refund_payment.transaction_id,
                    'refund_amount': refund_amount,
                    'original_transaction_id': original_transaction_id
                }
            else:
                refund_payment.write({
                    'state': 'failed',
                    'error_code': 'REFUND_FAILED',
                    'error_message': 'Refund processing failed',
                    'completed_at': request.env.cr.now(),
                })
                
                result = {
                    'success': False,
                    'error_code': 'REFUND_FAILED',
                    'error_message': 'Refund processing failed'
                }
            
            return result
            
        except Exception as e:
            _logger.error(f"Geidea refund processing failed: {str(e)}")
            return {
                'success': False,
                'error_code': 'SYSTEM_ERROR',
                'error_message': str(e)
            }

    @http.route('/pos/geidea/get_payment_status', type='json', auth='user')
    def get_payment_status(self, transaction_id):
        """Get the status of a Geidea payment transaction"""
        try:
            payment = request.env['geidea.payment'].search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
            
            if not payment:
                return {
                    'success': False,
                    'error': 'Transaction not found'
                }
            
            return {
                'success': True,
                'transaction_id': payment.transaction_id,
                'state': payment.state,
                'amount': payment.amount,
                'currency': payment.currency_id.name,
                'created_at': payment.create_date.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                'card_type': payment.card_type,
                'last_four_digits': payment.last_four_digits,
                'error_code': payment.error_code,
                'error_message': payment.error_message
            }
            
        except Exception as e:
            _logger.error(f"Failed to get payment status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/pos/geidea/device_discovery', type='json', auth='user')
    def device_discovery(self, **kwargs):
        """Simulate Bluetooth device discovery for Geidea devices"""
        try:
            # Simulate discovered devices
            devices = [
                {
                    'id': 'GEIDEA_TERMINAL_001',
                    'name': 'Geidea Terminal 001',
                    'model': 'GP-100',
                    'mac_address': '00:11:22:33:44:55',
                    'signal_strength': -45,
                    'battery_level': 85,
                    'status': 'available'
                },
                {
                    'id': 'GEIDEA_TERMINAL_002',
                    'name': 'Geidea Terminal 002',
                    'model': 'GP-200',
                    'mac_address': '00:11:22:33:44:66',
                    'signal_strength': -60,
                    'battery_level': 92,
                    'status': 'available'
                }
            ]
            
            return {
                'success': True,
                'devices': devices
            }
            
        except Exception as e:
            _logger.error(f"Device discovery failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }