# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


class GeideaPaymentController(http.Controller):
    """Controller for Geidea payment API endpoints"""
    
    @http.route('/geidea/test_connection', type='json', auth='user', methods=['POST'])
    def test_connection(self, **kwargs):
        """Test connection to Geidea payment gateway"""
        try:
            terminal_id = kwargs.get('terminal_id')
            service = request.env['geidea.payment.service']
            result = service.test_connection(terminal_id)
            return result
        except Exception as e:
            _logger.error(f"Connection test error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/initiate_payment', type='json', auth='user', methods=['POST'])
    def initiate_payment(self, **kwargs):
        """Initiate a payment transaction"""
        try:
            required_fields = ['amount', 'currency', 'payment_method']
            missing_fields = [field for field in required_fields if not kwargs.get(field)]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            service = request.env['geidea.payment.service']
            result = service.initiate_payment(kwargs)
            return result
            
        except Exception as e:
            _logger.error(f"Payment initiation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/capture_payment', type='json', auth='user', methods=['POST'])
    def capture_payment(self, **kwargs):
        """Capture an authorized payment"""
        try:
            transaction_id = kwargs.get('transaction_id')
            amount = kwargs.get('amount')
            
            if not transaction_id:
                return {'success': False, 'error': 'Transaction ID is required'}
            
            service = request.env['geidea.payment.service']
            result = service.capture_payment(transaction_id, amount)
            return result
            
        except Exception as e:
            _logger.error(f"Payment capture error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/refund_payment', type='json', auth='user', methods=['POST'])
    def refund_payment(self, **kwargs):
        """Process a payment refund"""
        try:
            transaction_id = kwargs.get('transaction_id')
            refund_amount = kwargs.get('refund_amount')
            reason = kwargs.get('reason')
            
            if not transaction_id or not refund_amount:
                return {
                    'success': False,
                    'error': 'Transaction ID and refund amount are required'
                }
            
            service = request.env['geidea.payment.service']
            result = service.refund_payment(transaction_id, refund_amount, reason)
            return result
            
        except Exception as e:
            _logger.error(f"Payment refund error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/check_status/<int:transaction_id>', type='json', auth='user', methods=['GET'])
    def check_transaction_status(self, transaction_id, **kwargs):
        """Check transaction status"""
        try:
            service = request.env['geidea.payment.service']
            result = service.check_transaction_status(transaction_id)
            return result
            
        except Exception as e:
            _logger.error(f"Status check error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/partial_payment', type='json', auth='user', methods=['POST'])
    def process_partial_payment(self, **kwargs):
        """Process a partial payment"""
        try:
            order_id = kwargs.get('order_id')
            payment_amount = kwargs.get('payment_amount')
            payment_method = kwargs.get('payment_method')
            
            if not all([order_id, payment_amount, payment_method]):
                return {
                    'success': False,
                    'error': 'Order ID, payment amount, and payment method are required'
                }
            
            service = request.env['geidea.payment.service']
            result = service.process_partial_payment(order_id, payment_amount, payment_method)
            return result
            
        except Exception as e:
            _logger.error(f"Partial payment error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/terminal_health/<string:terminal_id>', type='json', auth='user', methods=['GET'])
    def check_terminal_health(self, terminal_id, **kwargs):
        """Check terminal health status"""
        try:
            terminal_model = request.env['geidea.payment.terminal']
            result = terminal_model.check_terminal_health(terminal_id)
            return result
            
        except Exception as e:
            _logger.error(f"Terminal health check error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/transactions', type='json', auth='user', methods=['GET'])
    def get_transactions(self, **kwargs):
        """Get transaction history with filtering"""
        try:
            domain = []
            
            # Add filters based on parameters
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            if kwargs.get('date_from'):
                domain.append(('create_date', '>=', kwargs['date_from']))
            
            if kwargs.get('date_to'):
                domain.append(('create_date', '<=', kwargs['date_to']))
            
            if kwargs.get('terminal_id'):
                domain.append(('terminal_id.terminal_id', '=', kwargs['terminal_id']))
            
            limit = int(kwargs.get('limit', 50))
            offset = int(kwargs.get('offset', 0))
            
            transactions = request.env['geidea.payment.transaction'].search(
                domain, limit=limit, offset=offset, order='create_date desc'
            )
            
            transaction_data = []
            for trans in transactions:
                transaction_data.append({
                    'id': trans.id,
                    'name': trans.name,
                    'transaction_id': trans.transaction_id,
                    'amount': trans.amount,
                    'currency': trans.currency_id.name,
                    'payment_method': trans.payment_method,
                    'state': trans.state,
                    'created_at': trans.create_date.isoformat() if trans.create_date else None,
                    'completed_at': trans.completed_at.isoformat() if trans.completed_at else None,
                    'response_time': trans.response_time,
                    'error_message': trans.error_message
                })
            
            return {
                'success': True,
                'transactions': transaction_data,
                'total_count': len(transaction_data)
            }
            
        except Exception as e:
            _logger.error(f"Transaction retrieval error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/performance_metrics', type='json', auth='user', methods=['GET'])
    def get_performance_metrics(self, **kwargs):
        """Get performance metrics for terminals and transactions"""
        try:
            # Get transaction statistics
            transactions = request.env['geidea.payment.transaction'].search([])
            
            total_transactions = len(transactions)
            successful_transactions = len(transactions.filtered(lambda t: t.state in ['completed', 'captured']))
            failed_transactions = len(transactions.filtered(lambda t: t.state == 'failed'))
            
            success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
            
            # Calculate average response time
            completed_transactions = transactions.filtered(lambda t: t.response_time > 0)
            avg_response_time = sum(completed_transactions.mapped('response_time')) / len(completed_transactions) if completed_transactions else 0
            
            # Get terminal statistics
            terminals = request.env['geidea.payment.terminal'].search([])
            connected_terminals = len(terminals.filtered(lambda t: t.status == 'connected'))
            total_terminals = len(terminals)
            
            return {
                'success': True,
                'metrics': {
                    'total_transactions': total_transactions,
                    'successful_transactions': successful_transactions,
                    'failed_transactions': failed_transactions,
                    'success_rate': round(success_rate, 2),
                    'average_response_time': round(avg_response_time, 2),
                    'connected_terminals': connected_terminals,
                    'total_terminals': total_terminals,
                    'terminal_connectivity_rate': round((connected_terminals / total_terminals * 100) if total_terminals > 0 else 0, 2)
                }
            }
            
        except Exception as e:
            _logger.error(f"Performance metrics error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/config', type='json', auth='user', methods=['GET'])
    def get_geidea_config(self, **kwargs):
        """Get Geidea configuration (safe fields only)"""
        try:
            company = request.env.company
            
            if not company.enable_geidea_integration:
                return {'success': False, 'error': 'Geidea integration is not enabled'}
            
            config = {
                'enabled': company.enable_geidea_integration,
                'merchant_id': company.geidea_merchant_id,
                'terminal_id': company.geidea_terminal_id,
                'environment': company.geidea_environment,
                'connection_timeout': company.geidea_connection_timeout,
                'enable_partial_payments': company.geidea_enable_partial_payments,
                'enable_refunds': company.geidea_enable_refunds,
                'max_retry_attempts': company.geidea_max_retry_attempts,
                'connection_pool_size': company.geidea_connection_pool_size
            }
            
            return {'success': True, 'config': config}
            
        except Exception as e:
            _logger.error(f"Config retrieval error: {str(e)}")
            return {'success': False, 'error': str(e)}


class GeideaWebhookController(http.Controller):
    """Controller for handling Geidea webhook notifications"""
    
    @http.route('/geidea/webhook/payment_status', type='json', auth='none', methods=['POST'], csrf=False)
    def payment_status_webhook(self, **kwargs):
        """Handle payment status webhook from Geidea"""
        try:
            data = request.jsonrequest
            _logger.info(f"Received Geidea webhook: {data}")
            
            # Validate webhook signature if configured
            # This would typically involve verifying the signature using a shared secret
            
            transaction_id = data.get('transactionId')
            if not transaction_id:
                return {'success': False, 'error': 'Missing transaction ID'}
            
            # Find the transaction
            transaction = request.env['geidea.payment.transaction'].sudo().search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
            
            if not transaction:
                _logger.warning(f"Transaction not found for webhook: {transaction_id}")
                return {'success': False, 'error': 'Transaction not found'}
            
            # Update transaction status based on webhook data
            new_status = data.get('status')
            if new_status:
                status_mapping = {
                    'completed': 'completed',
                    'failed': 'failed',
                    'cancelled': 'cancelled',
                    'refunded': 'refunded'
                }
                
                mapped_status = status_mapping.get(new_status)
                if mapped_status and mapped_status != transaction.state:
                    transaction.write({
                        'state': mapped_status,
                        'completed_at': fields.Datetime.now() if mapped_status == 'completed' else transaction.completed_at
                    })
                    
                    _logger.info(f"Updated transaction {transaction.name} status to {mapped_status}")
            
            return {'success': True, 'message': 'Webhook processed successfully'}
            
        except Exception as e:
            _logger.error(f"Webhook processing error: {str(e)}")
            return {'success': False, 'error': str(e)}