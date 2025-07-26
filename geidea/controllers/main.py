# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import BadRequest

from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class GeideaPaymentController(http.Controller):
    
    @http.route(['/geidea/payment/create'], type='json', auth='user', methods=['POST'])
    def create_payment_transaction(self, **kwargs):
        """Create a new Geidea payment transaction"""
        try:
            acquirer_id = kwargs.get('acquirer_id')
            amount = float(kwargs.get('amount', 0))
            currency_id = kwargs.get('currency_id')
            pos_order_id = kwargs.get('pos_order_id')
            
            if not all([acquirer_id, amount, currency_id]):
                raise UserError(_('Missing required parameters'))
            
            acquirer = request.env['geidea.payment.acquirer'].browse(acquirer_id)
            if not acquirer.exists():
                raise UserError(_('Invalid acquirer'))
            
            # Generate unique transaction reference
            transaction_name = f"GEIDEA-{request.env['ir.sequence'].next_by_code('geidea.payment.transaction') or 'TXN'}"
            
            transaction = request.env['geidea.payment.transaction'].create({
                'name': transaction_name,
                'acquirer_id': acquirer_id,
                'amount': amount,
                'currency_id': currency_id,
                'pos_order_id': pos_order_id,
                'pos_session_id': kwargs.get('pos_session_id'),
            })
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'transaction_ref': transaction.name,
                'message': _('Transaction created successfully')
            }
            
        except Exception as e:
            _logger.error(f"Error creating Geidea transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Failed to create transaction')
            }
    
    @http.route(['/geidea/payment/process'], type='json', auth='user', methods=['POST'])
    def process_payment(self, **kwargs):
        """Process payment through Geidea API"""
        try:
            transaction_id = kwargs.get('transaction_id')
            if not transaction_id:
                raise UserError(_('Transaction ID is required'))
            
            transaction = request.env['geidea.payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                raise UserError(_('Transaction not found'))
            
            # Send payment request to Geidea
            result = transaction.send_payment_request()
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'geidea_transaction_id': transaction.geidea_transaction_id,
                'geidea_order_id': transaction.geidea_order_id,
                'status': transaction.state,
                'result': result,
                'message': _('Payment request sent successfully')
            }
            
        except Exception as e:
            _logger.error(f"Error processing Geidea payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Payment processing failed')
            }
    
    @http.route(['/geidea/payment/status'], type='json', auth='user', methods=['POST'])
    def check_payment_status(self, **kwargs):
        """Check payment transaction status"""
        try:
            transaction_id = kwargs.get('transaction_id')
            if not transaction_id:
                raise UserError(_('Transaction ID is required'))
            
            transaction = request.env['geidea.payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                raise UserError(_('Transaction not found'))
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'status': transaction.state,
                'amount': transaction.amount,
                'currency': transaction.currency_id.name,
                'geidea_transaction_id': transaction.geidea_transaction_id,
                'error_message': transaction.error_message,
                'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            }
            
        except Exception as e:
            _logger.error(f"Error checking Geidea payment status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Failed to check payment status')
            }
    
    @http.route(['/geidea/payment/capture'], type='json', auth='user', methods=['POST'])
    def capture_payment(self, **kwargs):
        """Capture authorized payment"""
        try:
            transaction_id = kwargs.get('transaction_id')
            if not transaction_id:
                raise UserError(_('Transaction ID is required'))
            
            transaction = request.env['geidea.payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                raise UserError(_('Transaction not found'))
            
            transaction.capture_payment()
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'status': transaction.state,
                'message': _('Payment captured successfully')
            }
            
        except Exception as e:
            _logger.error(f"Error capturing Geidea payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Payment capture failed')
            }
    
    @http.route(['/geidea/payment/cancel'], type='json', auth='user', methods=['POST'])
    def cancel_payment(self, **kwargs):
        """Cancel payment transaction"""
        try:
            transaction_id = kwargs.get('transaction_id')
            if not transaction_id:
                raise UserError(_('Transaction ID is required'))
            
            transaction = request.env['geidea.payment.transaction'].browse(transaction_id)
            if not transaction.exists():
                raise UserError(_('Transaction not found'))
            
            transaction.cancel_payment()
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'status': transaction.state,
                'message': _('Payment cancelled successfully')
            }
            
        except Exception as e:
            _logger.error(f"Error cancelling Geidea payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Payment cancellation failed')
            }
    
    @http.route(['/geidea/payment/callback'], type='http', auth='public', methods=['POST'], csrf=False)
    def payment_callback(self, **kwargs):
        """Handle Geidea payment callback"""
        try:
            # Parse callback data
            callback_data = request.httprequest.get_json() or kwargs
            
            transaction_ref = callback_data.get('merchantReferenceId')
            geidea_transaction_id = callback_data.get('transactionId')
            status = callback_data.get('status')
            
            if not transaction_ref:
                _logger.error("Geidea callback: Missing transaction reference")
                return "Missing transaction reference", 400
            
            # Find transaction
            transaction = request.env['geidea.payment.transaction'].sudo().search([
                ('name', '=', transaction_ref)
            ], limit=1)
            
            if not transaction:
                _logger.error(f"Geidea callback: Transaction not found: {transaction_ref}")
                return "Transaction not found", 404
            
            # Update transaction status based on callback
            if status == 'AUTHORIZED':
                transaction.state = 'authorized'
                transaction.authorized_date = request.env.cr.now()
            elif status == 'CAPTURED':
                transaction.state = 'captured'
                transaction.captured_date = request.env.cr.now()
            elif status == 'CANCELLED':
                transaction.state = 'cancelled'
            elif status == 'FAILED':
                transaction.state = 'error'
                transaction.error_message = callback_data.get('message', 'Payment failed')
            
            # Update Geidea transaction ID if provided
            if geidea_transaction_id:
                transaction.geidea_transaction_id = geidea_transaction_id
            
            # Store callback response
            transaction.response_data = json.dumps(callback_data, indent=2)
            
            _logger.info(f"Geidea callback processed for transaction {transaction_ref}: {status}")
            return "OK", 200
            
        except Exception as e:
            _logger.error(f"Error processing Geidea callback: {str(e)}")
            return "Internal server error", 500
    
    @http.route(['/geidea/payment/return'], type='http', auth='public', methods=['GET'])
    def payment_return(self, **kwargs):
        """Handle Geidea payment return URL"""
        try:
            transaction_ref = kwargs.get('merchantReferenceId')
            status = kwargs.get('status')
            
            if transaction_ref:
                transaction = request.env['geidea.payment.transaction'].sudo().search([
                    ('name', '=', transaction_ref)
                ], limit=1)
                
                if transaction and transaction.pos_order_id:
                    # Redirect to POS order or appropriate page
                    return request.redirect(f'/web#id={transaction.pos_order_id.id}&model=pos.order&view_type=form')
            
            # Default redirect to POS
            return request.redirect('/pos/web')
            
        except Exception as e:
            _logger.error(f"Error handling Geidea return: {str(e)}")
            return request.redirect('/pos/web')
    
    @http.route(['/geidea/acquirer/test'], type='json', auth='user', methods=['POST'])
    def test_acquirer_connection(self, **kwargs):
        """Test Geidea acquirer connection"""
        try:
            acquirer_id = kwargs.get('acquirer_id')
            if not acquirer_id:
                raise UserError(_('Acquirer ID is required'))
            
            acquirer = request.env['geidea.payment.acquirer'].browse(acquirer_id)
            if not acquirer.exists():
                raise UserError(_('Acquirer not found'))
            
            result = acquirer.test_connection()
            
            return {
                'success': True,
                'connection_status': acquirer.connection_status,
                'message': _('Connection test completed'),
                'result': result
            }
            
        except Exception as e:
            _logger.error(f"Error testing Geidea connection: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Connection test failed')
            }
    
    @http.route(['/geidea/pos/acquirers'], type='json', auth='user', methods=['GET'])
    def get_pos_acquirers(self, **kwargs):
        """Get Geidea acquirers for POS"""
        try:
            pos_config_id = kwargs.get('pos_config_id')
            
            domain = [('active', '=', True)]
            if pos_config_id:
                domain.append(('pos_config_ids', 'in', pos_config_id))
            
            acquirers = request.env['geidea.payment.acquirer'].search_read(
                domain,
                ['id', 'name', 'merchant_id', 'terminal_id', 'environment', 'currency_id']
            )
            
            return {
                'success': True,
                'acquirers': acquirers,
                'message': _('Acquirers loaded successfully')
            }
            
        except Exception as e:
            _logger.error(f"Error loading Geidea acquirers: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': _('Failed to load acquirers')
            }