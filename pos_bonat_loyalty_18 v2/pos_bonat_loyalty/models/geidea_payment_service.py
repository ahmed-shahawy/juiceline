# -*- coding: utf-8 -*-
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

_logger = logging.getLogger(__name__)


class GeideaPaymentService(models.Model):
    """Service class to handle Geidea payment operations"""
    _name = 'geidea.payment.service'
    _description = 'Geidea Payment Service'
    
    # Connection pool management
    _connection_pools = {}
    _pool_lock = threading.Lock()
    
    @api.model
    def get_geidea_config(self):
        """Get Geidea configuration from company settings"""
        company = self.env.company
        if not company.enable_geidea_integration:
            raise UserError(_("Geidea integration is not enabled"))
        
        required_fields = ['geidea_api_key', 'geidea_merchant_id', 'geidea_terminal_id']
        missing_fields = [field for field in required_fields if not getattr(company, field)]
        
        if missing_fields:
            raise UserError(_("Missing Geidea configuration: %s") % ', '.join(missing_fields))
        
        base_url = "https://api-sandbox.geidea.net" if company.geidea_environment == 'test' else "https://api.geidea.net"
        
        return {
            'api_key': company.geidea_api_key,
            'api_password': company.geidea_api_password,
            'merchant_id': company.geidea_merchant_id,
            'terminal_id': company.geidea_terminal_id,
            'base_url': base_url,
            'timeout': company.geidea_connection_timeout,
            'max_retries': company.geidea_max_retry_attempts,
            'enable_partial_payments': company.geidea_enable_partial_payments,
            'enable_refunds': company.geidea_enable_refunds
        }
    
    @api.model
    def create_session(self, config=None):
        """Create HTTP session with retry strategy and connection pooling"""
        if not config:
            config = self.get_geidea_config()
        
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config.get('max_retries', 3),
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.env.company.geidea_connection_pool_size,
            pool_maxsize=self.env.company.geidea_connection_pool_size
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set authentication headers
        session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["api_key"]}',
            'X-Merchant-ID': config['merchant_id']
        })
        
        return session
    
    @api.model
    def test_connection(self, terminal_id=None):
        """Test connection to Geidea payment gateway"""
        try:
            config = self.get_geidea_config()
            session = self.create_session(config)
            
            # Ping endpoint to test connectivity
            url = f"{config['base_url']}/api/v1/ping"
            
            start_time = time.time()
            response = session.get(url, timeout=config['timeout'])
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                # Update terminal status if terminal_id provided
                if terminal_id:
                    terminal = self.env['geidea.payment.terminal'].search([('terminal_id', '=', terminal_id)], limit=1)
                    if terminal:
                        terminal.write({
                            'status': 'connected',
                            'last_connection': fields.Datetime.now(),
                            'connection_attempts': 0,
                            'error_message': False,
                            'average_response_time': response_time
                        })
                
                return {
                    'success': True,
                    'message': _('Connection successful'),
                    'response_time': response_time,
                    'status': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': _('Connection failed'),
                    'error': response.text,
                    'status': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Geidea connection test failed: {str(e)}")
            
            # Update terminal status on error
            if terminal_id:
                terminal = self.env['geidea.payment.terminal'].search([('terminal_id', '=', terminal_id)], limit=1)
                if terminal:
                    terminal.write({
                        'status': 'error',
                        'connection_attempts': terminal.connection_attempts + 1,
                        'error_message': str(e)
                    })
            
            return {
                'success': False,
                'message': _('Connection error'),
                'error': str(e)
            }
    
    @api.model
    def initiate_payment(self, payment_data):
        """Initiate a payment transaction with Geidea"""
        try:
            # Validate payment data
            required_fields = ['amount', 'currency', 'payment_method']
            missing_fields = [field for field in required_fields if not payment_data.get(field)]
            
            if missing_fields:
                raise ValidationError(_("Missing payment data: %s") % ', '.join(missing_fields))
            
            config = self.get_geidea_config()
            session = self.create_session(config)
            
            # Create transaction record
            transaction = self.env['geidea.payment.transaction'].create({
                'amount': payment_data['amount'],
                'currency_id': payment_data.get('currency_id'),
                'payment_method': payment_data['payment_method'],
                'pos_order_id': payment_data.get('pos_order_id'),
                'state': 'pending'
            })
            
            # Prepare Geidea API request
            geidea_payload = {
                'amount': payment_data['amount'],
                'currency': payment_data['currency'],
                'merchantId': config['merchant_id'],
                'terminalId': config['terminal_id'],
                'transactionId': transaction.name,
                'paymentMethod': payment_data['payment_method'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Add optional fields
            if payment_data.get('customer_email'):
                geidea_payload['customerEmail'] = payment_data['customer_email']
            if payment_data.get('customer_phone'):
                geidea_payload['customerPhone'] = payment_data['customer_phone']
            
            url = f"{config['base_url']}/api/v1/payments/initiate"
            
            start_time = time.time()
            response = session.post(url, json=geidea_payload, timeout=config['timeout'])
            response_time = (time.time() - start_time) * 1000
            
            transaction.write({
                'response_time': response_time,
                'state': 'processing'
            })
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('status') == 'success':
                    transaction.write({
                        'transaction_id': response_data.get('transactionId'),
                        'state': 'authorized',
                        'authorized_at': fields.Datetime.now()
                    })
                    
                    return {
                        'success': True,
                        'transaction_id': transaction.id,
                        'geidea_transaction_id': response_data.get('transactionId'),
                        'status': 'authorized',
                        'data': response_data
                    }
                else:
                    transaction.write({
                        'state': 'failed',
                        'error_code': response_data.get('errorCode'),
                        'error_message': response_data.get('errorMessage')
                    })
                    
                    return {
                        'success': False,
                        'error': response_data.get('errorMessage', 'Payment failed'),
                        'error_code': response_data.get('errorCode')
                    }
            else:
                transaction.write({
                    'state': 'failed',
                    'error_message': f"HTTP {response.status_code}: {response.text}"
                })
                
                return {
                    'success': False,
                    'error': f"Payment request failed: {response.text}",
                    'status_code': response.status_code
                }
                
        except Exception as e:
            _logger.error(f"Payment initiation failed: {str(e)}")
            
            if 'transaction' in locals():
                transaction.write({
                    'state': 'failed',
                    'error_message': str(e)
                })
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @api.model
    def capture_payment(self, transaction_id, amount=None):
        """Capture an authorized payment"""
        try:
            transaction = self.env['geidea.payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                return {'success': False, 'error': 'Transaction not found'}
            
            if transaction.state != 'authorized':
                return {'success': False, 'error': 'Transaction not in authorized state'}
            
            config = self.get_geidea_config()
            session = self.create_session(config)
            
            capture_amount = amount or transaction.amount
            
            payload = {
                'transactionId': transaction.transaction_id,
                'amount': capture_amount,
                'merchantId': config['merchant_id']
            }
            
            url = f"{config['base_url']}/api/v1/payments/capture"
            response = session.post(url, json=payload, timeout=config['timeout'])
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('status') == 'success':
                    transaction.write({
                        'state': 'captured',
                        'completed_at': fields.Datetime.now()
                    })
                    
                    return {
                        'success': True,
                        'transaction_id': transaction_id,
                        'captured_amount': capture_amount,
                        'data': response_data
                    }
                else:
                    return {
                        'success': False,
                        'error': response_data.get('errorMessage', 'Capture failed')
                    }
            else:
                return {
                    'success': False,
                    'error': f"Capture request failed: {response.text}"
                }
                
        except Exception as e:
            _logger.error(f"Payment capture failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @api.model
    def refund_payment(self, transaction_id, refund_amount, reason=None):
        """Process a refund for a completed payment"""
        try:
            original_transaction = self.env['geidea.payment.transaction'].browse(transaction_id)
            if not original_transaction.exists():
                return {'success': False, 'error': 'Original transaction not found'}
            
            if original_transaction.state not in ['captured', 'completed']:
                return {'success': False, 'error': 'Transaction not eligible for refund'}
            
            config = self.get_geidea_config()
            if not config['enable_refunds']:
                return {'success': False, 'error': 'Refunds are not enabled'}
            
            session = self.create_session(config)
            
            # Create refund transaction record
            refund_transaction = self.env['geidea.payment.transaction'].create({
                'amount': refund_amount,
                'currency_id': original_transaction.currency_id.id,
                'payment_method': original_transaction.payment_method,
                'original_transaction_id': original_transaction.id,
                'refund_amount': refund_amount,
                'refund_reason': reason,
                'state': 'pending'
            })
            
            payload = {
                'originalTransactionId': original_transaction.transaction_id,
                'refundAmount': refund_amount,
                'reason': reason or 'Customer refund',
                'merchantId': config['merchant_id']
            }
            
            url = f"{config['base_url']}/api/v1/payments/refund"
            response = session.post(url, json=payload, timeout=config['timeout'])
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('status') == 'success':
                    refund_transaction.write({
                        'transaction_id': response_data.get('refundTransactionId'),
                        'state': 'completed',
                        'completed_at': fields.Datetime.now()
                    })
                    
                    # Update original transaction status
                    if refund_amount >= original_transaction.amount:
                        original_transaction.write({'state': 'refunded'})
                    else:
                        original_transaction.write({'state': 'partially_refunded'})
                    
                    return {
                        'success': True,
                        'refund_transaction_id': refund_transaction.id,
                        'geidea_refund_id': response_data.get('refundTransactionId'),
                        'data': response_data
                    }
                else:
                    refund_transaction.write({
                        'state': 'failed',
                        'error_message': response_data.get('errorMessage')
                    })
                    
                    return {
                        'success': False,
                        'error': response_data.get('errorMessage', 'Refund failed')
                    }
            else:
                refund_transaction.write({
                    'state': 'failed',
                    'error_message': f"HTTP {response.status_code}: {response.text}"
                })
                
                return {
                    'success': False,
                    'error': f"Refund request failed: {response.text}"
                }
                
        except Exception as e:
            _logger.error(f"Payment refund failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @api.model
    def check_transaction_status(self, transaction_id):
        """Check the status of a transaction with Geidea"""
        try:
            transaction = self.env['geidea.payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                return {'success': False, 'error': 'Transaction not found'}
            
            if not transaction.transaction_id:
                return {'success': False, 'error': 'No Geidea transaction ID found'}
            
            config = self.get_geidea_config()
            session = self.create_session(config)
            
            url = f"{config['base_url']}/api/v1/payments/status/{transaction.transaction_id}"
            response = session.get(url, timeout=config['timeout'])
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Update transaction status based on Geidea response
                geidea_status = response_data.get('status')
                if geidea_status:
                    status_mapping = {
                        'pending': 'pending',
                        'authorized': 'authorized', 
                        'captured': 'captured',
                        'completed': 'completed',
                        'failed': 'failed',
                        'cancelled': 'cancelled',
                        'refunded': 'refunded'
                    }
                    
                    new_status = status_mapping.get(geidea_status, transaction.state)
                    if new_status != transaction.state:
                        transaction.write({'state': new_status})
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'status': transaction.state,
                    'geidea_data': response_data
                }
            else:
                return {
                    'success': False,
                    'error': f"Status check failed: {response.text}"
                }
                
        except Exception as e:
            _logger.error(f"Transaction status check failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @api.model
    def process_partial_payment(self, order_id, payment_amount, payment_method):
        """Process a partial payment for an order"""
        try:
            config = self.get_geidea_config()
            if not config['enable_partial_payments']:
                return {'success': False, 'error': 'Partial payments are not enabled'}
            
            order = self.env['pos.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Order not found'}
            
            remaining_amount = order.amount_total - order.amount_paid
            if payment_amount > remaining_amount:
                return {'success': False, 'error': 'Payment amount exceeds remaining balance'}
            
            # Initiate partial payment
            payment_data = {
                'amount': payment_amount,
                'currency': order.currency_id.name,
                'currency_id': order.currency_id.id,
                'payment_method': payment_method,
                'pos_order_id': order_id
            }
            
            result = self.initiate_payment(payment_data)
            
            if result['success']:
                # If successful, capture the payment immediately for partial payments
                capture_result = self.capture_payment(result['transaction_id'])
                if capture_result['success']:
                    return {
                        'success': True,
                        'transaction_id': result['transaction_id'],
                        'amount_paid': payment_amount,
                        'remaining_amount': remaining_amount - payment_amount
                    }
                else:
                    return capture_result
            else:
                return result
                
        except Exception as e:
            _logger.error(f"Partial payment processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}