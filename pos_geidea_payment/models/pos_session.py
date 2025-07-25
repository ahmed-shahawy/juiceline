# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import json

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Add Geidea models to POS UI"""
        result = super()._pos_ui_models_to_load()
        result.append('geidea.terminal')
        return result

    def _loader_params_geidea_terminal(self):
        """Define parameters for loading Geidea terminals"""
        return {
            'search_params': {
                'domain': [('pos_config_ids', 'in', self.config_id.id), ('active', '=', True)],
                'fields': [
                    'name', 'terminal_id', 'merchant_id', 'connection_type', 
                    'platform', 'connection_status', 'ip_address', 'port', 
                    'bluetooth_address', 'serial_port', 'usb_vendor_id', 
                    'usb_product_id', 'timeout', 'retry_attempts', 'auto_reconnect'
                ],
            },
        }

    def _get_pos_ui_geidea_terminal(self, params):
        """Load Geidea terminals for POS UI"""
        terminals = self.env['geidea.terminal'].search_read(**params['search_params'])
        # Add connection config for each terminal
        for terminal in terminals:
            terminal_obj = self.env['geidea.terminal'].browse(terminal['id'])
            terminal['connection_config'] = terminal_obj.get_connection_config()
        return terminals

    def get_geidea_config(self):
        """Get complete Geidea configuration for this session"""
        self.ensure_one()
        return self.config_id._get_geidea_terminal_config()

    @api.model
    def geidea_payment_request(self, payment_data):
        """Process Geidea payment request"""
        try:
            terminal_id = payment_data.get('terminal_id')
            amount = payment_data.get('amount')
            currency = payment_data.get('currency', 'SAR')
            
            if not terminal_id:
                return {'success': False, 'error': _('Terminal ID is required')}
            
            if not amount or amount <= 0:
                return {'success': False, 'error': _('Invalid amount')}
            
            terminal = self.env['geidea.terminal'].browse(terminal_id)
            if not terminal.exists():
                return {'success': False, 'error': _('Terminal not found')}
            
            # Process payment through terminal
            result = self._process_geidea_payment(terminal, amount, currency, payment_data)
            return result
            
        except Exception as e:
            _logger.error(f"Geidea payment request failed: {e}")
            return {'success': False, 'error': str(e)}

    def _process_geidea_payment(self, terminal, amount, currency, payment_data):
        """Process payment through Geidea terminal"""
        # This is where the actual payment processing logic will be implemented
        # For now, return a success response for testing
        transaction_id = f"GDA{self.id}{int(fields.Datetime.now().timestamp())}"
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': currency,
            'terminal_id': terminal.terminal_id,
            'status': 'approved',
            'receipt_data': {
                'merchant_id': terminal.merchant_id,
                'terminal_id': terminal.terminal_id,
                'transaction_id': transaction_id,
                'amount': amount,
                'currency': currency,
                'timestamp': fields.Datetime.now().isoformat(),
            }
        }

    @api.model
    def geidea_terminal_status(self, terminal_id):
        """Get terminal connection status"""
        try:
            terminal = self.env['geidea.terminal'].browse(terminal_id)
            if not terminal.exists():
                return {'success': False, 'error': _('Terminal not found')}
            
            return {
                'success': True,
                'terminal_id': terminal.terminal_id,
                'status': terminal.connection_status,
                'last_test': terminal.last_connection_test,
                'error': terminal.last_error_message,
            }
        except Exception as e:
            _logger.error(f"Terminal status check failed: {e}")
            return {'success': False, 'error': str(e)}

    @api.model  
    def geidea_test_connection(self, terminal_id):
        """Test terminal connection"""
        try:
            terminal = self.env['geidea.terminal'].browse(terminal_id)
            if not terminal.exists():
                return {'success': False, 'error': _('Terminal not found')}
            
            return terminal.test_connection()
        except Exception as e:
            _logger.error(f"Terminal connection test failed: {e}")
            return {'success': False, 'error': str(e)}