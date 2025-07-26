# -*- coding: utf-8 -*-
import json
import logging
import pprint
import werkzeug

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):

    @http.route('/payment/geidea/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_webhook(self, **kwargs):
        """Handle webhook notifications from Geidea."""
        _logger.info('Geidea webhook received with data:\n%s', pprint.pformat(kwargs))
        
        try:
            # Get JSON data from request
            if request.httprequest.content_type == 'application/json':
                data = json.loads(request.httprequest.data.decode('utf-8'))
            else:
                data = kwargs

            # Validate webhook signature if present
            if not self._verify_webhook_signature(data):
                _logger.warning('Geidea webhook signature verification failed')
                return werkzeug.Response('Signature verification failed', status=400)

            # Find and process the transaction
            transaction = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data('geidea', data)
            if transaction:
                transaction._process_feedback_data(data)
                _logger.info('Geidea webhook processed successfully for transaction %s', transaction.reference)
            else:
                _logger.warning('Geidea webhook: transaction not found for data %s', data)
                return werkzeug.Response('Transaction not found', status=404)

            return werkzeug.Response('OK', status=200)

        except ValidationError as e:
            _logger.error('Geidea webhook validation error: %s', str(e))
            return werkzeug.Response('Validation error', status=400)
        except Exception as e:
            _logger.error('Geidea webhook processing error: %s', str(e))
            return werkzeug.Response('Processing error', status=500)

    @http.route('/payment/geidea/return', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def geidea_return(self, **kwargs):
        """Handle return from Geidea payment page."""
        _logger.info('Geidea return received with data:\n%s', pprint.pformat(kwargs))
        
        try:
            # Process return data
            transaction = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data('geidea', kwargs)
            if transaction:
                transaction._process_feedback_data(kwargs)
                
                # Redirect based on transaction state
                if transaction.state == 'done':
                    return request.redirect('/payment/status/success')
                elif transaction.state == 'cancel':
                    return request.redirect('/payment/status/cancel')
                else:
                    return request.redirect('/payment/status/pending')
            else:
                _logger.warning('Geidea return: transaction not found for data %s', kwargs)
                return request.redirect('/payment/status/error')

        except Exception as e:
            _logger.error('Geidea return processing error: %s', str(e))
            return request.redirect('/payment/status/error')

    @http.route('/payment/geidea/cancel', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def geidea_cancel(self, **kwargs):
        """Handle cancellation from Geidea payment page."""
        _logger.info('Geidea cancel received with data:\n%s', pprint.pformat(kwargs))
        
        try:
            transaction = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data('geidea', kwargs)
            if transaction:
                transaction._set_canceled()
                _logger.info('Geidea payment cancelled for transaction %s', transaction.reference)
            
            return request.redirect('/payment/status/cancel')

        except Exception as e:
            _logger.error('Geidea cancel processing error: %s', str(e))
            return request.redirect('/payment/status/error')

    @http.route('/payment/geidea/pos/status', type='json', auth='user', methods=['POST'])
    def geidea_pos_payment_status(self, session_id, payment_method_id):
        """Check POS payment status for Geidea terminal."""
        try:
            payment_method = request.env['pos.payment.method'].browse(payment_method_id)
            if not payment_method.exists() or payment_method.use_payment_terminal != 'geidea':
                return {'error': 'Invalid payment method'}

            status = payment_method.geidea_pos_check_status(session_id)
            return status

        except Exception as e:
            _logger.error('Geidea POS status check error: %s', str(e))
            return {'error': str(e)}

    @http.route('/payment/geidea/pos/initiate', type='json', auth='user', methods=['POST'])
    def geidea_pos_initiate_payment(self, amount, currency, reference, payment_method_id):
        """Initiate POS payment on Geidea terminal."""
        try:
            payment_method = request.env['pos.payment.method'].browse(payment_method_id)
            if not payment_method.exists() or payment_method.use_payment_terminal != 'geidea':
                return {'error': 'Invalid payment method'}

            result = payment_method.geidea_pos_payment_request(amount, currency, reference)
            return result

        except Exception as e:
            _logger.error('Geidea POS payment initiation error: %s', str(e))
            return {'error': str(e)}

    @http.route('/payment/geidea/pos/cancel', type='json', auth='user', methods=['POST'])
    def geidea_pos_cancel_payment(self, session_id, payment_method_id):
        """Cancel POS payment on Geidea terminal."""
        try:
            payment_method = request.env['pos.payment.method'].browse(payment_method_id)
            if not payment_method.exists() or payment_method.use_payment_terminal != 'geidea':
                return {'error': 'Invalid payment method'}

            success = payment_method.geidea_pos_cancel_payment(session_id)
            return {'success': success}

        except Exception as e:
            _logger.error('Geidea POS payment cancellation error: %s', str(e))
            return {'error': str(e)}

    def _verify_webhook_signature(self, data):
        """Verify webhook signature from Geidea (if implemented)."""
        # This would implement signature verification if Geidea provides it
        # For now, we'll return True as basic implementation
        return True

    @http.route('/payment/geidea/test', type='http', auth='user', methods=['GET'])
    def geidea_test_connection(self):
        """Test connection to Geidea API (for admin users)."""
        if not request.env.user.has_group('base.group_system'):
            return werkzeug.Response('Unauthorized', status=403)

        try:
            acquirers = request.env['payment.acquirer'].search([('provider', '=', 'geidea')])
            results = []
            
            for acquirer in acquirers:
                try:
                    # Test API connection with a simple request
                    test_data = {
                        'merchantId': acquirer.geidea_merchant_id,
                        'test': True,
                    }
                    response = acquirer._geidea_make_request('pgw/api/v1/direct/test', test_data)
                    results.append({
                        'acquirer': acquirer.name,
                        'status': 'connected',
                        'response': response,
                    })
                except Exception as e:
                    results.append({
                        'acquirer': acquirer.name,
                        'status': 'error',
                        'error': str(e),
                    })

            return werkzeug.Response(
                json.dumps(results, indent=2),
                headers={'Content-Type': 'application/json'}
            )

        except Exception as e:
            return werkzeug.Response(
                json.dumps({'error': str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )