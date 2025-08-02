# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):

    @http.route('/payment/geidea/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_webhook(self, **kwargs):
        """Handle Geidea webhook notifications"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            _logger.info('Received Geidea webhook: %s', data)
            
            # Find the transaction
            transaction_id = data.get('transactionId')
            if not transaction_id:
                _logger.error('No transaction ID in webhook data')
                return 'Error: No transaction ID'
            
            # Process the webhook
            transaction = request.env['geidea.transaction'].sudo().search([
                ('transaction_id', '=', transaction_id)
            ], limit=1)
            
            if transaction:
                transaction._process_webhook_data(data)
                return 'OK'
            else:
                _logger.warning('Transaction not found for ID: %s', transaction_id)
                return 'Transaction not found'
                
        except Exception as e:
            _logger.error('Error processing Geidea webhook: %s', str(e))
            return 'Error'

    @http.route('/payment/geidea/return', type='http', auth='public', methods=['GET', 'POST'])
    def geidea_return(self, **kwargs):
        """Handle return from Geidea payment page"""
        try:
            _logger.info('Geidea return with data: %s', kwargs)
            
            # Extract transaction reference
            reference = kwargs.get('reference') or kwargs.get('order_id')
            if not reference:
                return request.redirect('/payment/process')
            
            # Find and update the payment transaction
            payment_tx = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference)
            ], limit=1)
            
            if payment_tx:
                payment_tx._handle_geidea_return_data(kwargs)
            
            return request.redirect('/payment/process')
            
        except Exception as e:
            _logger.error('Error processing Geidea return: %s', str(e))
            return request.redirect('/payment/process?error=1')

    @http.route('/payment/geidea/cancel', type='http', auth='public', methods=['GET', 'POST'])
    def geidea_cancel(self, **kwargs):
        """Handle cancellation from Geidea payment page"""
        _logger.info('Geidea payment cancelled: %s', kwargs)
        
        reference = kwargs.get('reference') or kwargs.get('order_id')
        if reference:
            payment_tx = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference)
            ], limit=1)
            
            if payment_tx:
                payment_tx._set_canceled()
        
        return request.redirect('/payment/process?cancelled=1')