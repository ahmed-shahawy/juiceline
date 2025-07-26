# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    # Geidea specific fields for POS integration
    use_payment_terminal = fields.Selection(
        selection_add=[('geidea', 'Geidea Payment Terminal')],
        ondelete={'geidea': 'set default'}
    )
    
    geidea_terminal_id = fields.Char(
        string='Terminal ID',
        help='Geidea terminal identifier for POS payments'
    )
    geidea_terminal_key = fields.Char(
        string='Terminal Key',
        help='Geidea terminal authentication key'
    )
    geidea_pos_api_url = fields.Char(
        string='POS API URL',
        default='https://api.merchant.geidea.net/pos',
        help='Geidea POS API endpoint URL'
    )

    @api.constrains('use_payment_terminal', 'geidea_terminal_id', 'geidea_terminal_key')
    def _check_geidea_terminal_config(self):
        """Validate Geidea terminal configuration."""
        for method in self:
            if method.use_payment_terminal == 'geidea':
                if not method.geidea_terminal_id:
                    raise ValidationError(_('Terminal ID is required for Geidea payment terminal.'))
                if not method.geidea_terminal_key:
                    raise ValidationError(_('Terminal Key is required for Geidea payment terminal.'))

    def _geidea_pos_make_request(self, endpoint, data):
        """Make request to Geidea POS API."""
        import requests
        import json
        
        url = f"{self.geidea_pos_api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.geidea_terminal_key}',
        }
        
        # Add terminal ID to data
        data['terminalId'] = self.geidea_terminal_id
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error('Geidea POS API request failed: %s', str(e))
            raise UserError(_('Payment terminal communication failed. Please try again.'))

    def geidea_pos_payment_request(self, amount, currency, reference):
        """Initiate payment request to Geidea terminal."""
        self.ensure_one()
        
        if self.use_payment_terminal != 'geidea':
            return False

        payment_data = {
            'amount': amount,
            'currency': currency,
            'reference': reference,
            'operation': 'sale',
            'timeout': 60,  # Payment timeout in seconds
        }

        try:
            response = self._geidea_pos_make_request('payment/initiate', payment_data)
            return {
                'status': 'success',
                'session_id': response.get('sessionId'),
                'terminal_response': response,
            }
        except Exception as e:
            _logger.error('Geidea POS payment initiation failed: %s', str(e))
            return {
                'status': 'error',
                'error': str(e),
            }

    def geidea_pos_check_status(self, session_id):
        """Check payment status on Geidea terminal."""
        self.ensure_one()
        
        if self.use_payment_terminal != 'geidea':
            return False

        try:
            response = self._geidea_pos_make_request('payment/status', {'sessionId': session_id})
            return {
                'status': response.get('status'),
                'transaction_id': response.get('transactionId'),
                'response_code': response.get('responseCode'),
                'response_message': response.get('responseMessage'),
                'card_info': response.get('cardInfo', {}),
            }
        except Exception as e:
            _logger.error('Geidea POS status check failed: %s', str(e))
            return {
                'status': 'error',
                'error': str(e),
            }

    def geidea_pos_cancel_payment(self, session_id):
        """Cancel payment on Geidea terminal."""
        self.ensure_one()
        
        if self.use_payment_terminal != 'geidea':
            return False

        try:
            response = self._geidea_pos_make_request('payment/cancel', {'sessionId': session_id})
            return response.get('status') == 'cancelled'
        except Exception as e:
            _logger.error('Geidea POS payment cancellation failed: %s', str(e))
            return False

    def geidea_pos_refund(self, transaction_id, amount, currency):
        """Process refund through Geidea terminal."""
        self.ensure_one()
        
        if self.use_payment_terminal != 'geidea':
            return False

        refund_data = {
            'originalTransactionId': transaction_id,
            'amount': amount,
            'currency': currency,
            'operation': 'refund',
        }

        try:
            response = self._geidea_pos_make_request('payment/refund', refund_data)
            return {
                'status': 'success' if response.get('responseCode') == '000' else 'failed',
                'refund_transaction_id': response.get('transactionId'),
                'response_message': response.get('responseMessage'),
            }
        except Exception as e:
            _logger.error('Geidea POS refund failed: %s', str(e))
            return {
                'status': 'error',
                'error': str(e),
            }


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _get_geidea_payment_methods(self):
        """Get Geidea payment methods configured for this POS."""
        return self.payment_method_ids.filtered(
            lambda pm: pm.use_payment_terminal == 'geidea'
        )

    def geidea_test_connection(self):
        """Test connection to Geidea payment terminals."""
        geidea_methods = self._get_geidea_payment_methods()
        
        if not geidea_methods:
            raise UserError(_('No Geidea payment methods configured for this POS.'))

        results = []
        for method in geidea_methods:
            try:
                # Test connection with a simple terminal status request
                response = method._geidea_pos_make_request('terminal/status', {})
                results.append({
                    'method': method.name,
                    'status': 'connected',
                    'terminal_id': method.geidea_terminal_id,
                    'response': response,
                })
            except Exception as e:
                results.append({
                    'method': method.name,
                    'status': 'error',
                    'terminal_id': method.geidea_terminal_id,
                    'error': str(e),
                })

        return results