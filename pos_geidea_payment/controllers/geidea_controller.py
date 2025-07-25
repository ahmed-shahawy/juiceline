# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):

    @http.route('/pos/geidea/payment', type='json', auth='user', methods=['POST'])
    def geidea_payment(self, **kwargs):
        """Handle Geidea payment requests from POS"""
        try:
            session = request.env['pos.session'].browse(kwargs.get('session_id'))
            if not session:
                return {'success': False, 'error': 'Invalid session'}
            
            return session.geidea_payment_request(kwargs)
        except Exception as e:
            _logger.error(f"Geidea payment endpoint error: {e}")
            return {'success': False, 'error': str(e)}

    @http.route('/pos/geidea/terminal/status', type='json', auth='user', methods=['POST'])
    def terminal_status(self, **kwargs):
        """Get terminal connection status"""
        try:
            return request.env['pos.session'].geidea_terminal_status(kwargs.get('terminal_id'))
        except Exception as e:
            _logger.error(f"Terminal status endpoint error: {e}")
            return {'success': False, 'error': str(e)}

    @http.route('/pos/geidea/terminal/test', type='json', auth='user', methods=['POST'])
    def test_connection(self, **kwargs):
        """Test terminal connection"""
        try:
            return request.env['pos.session'].geidea_test_connection(kwargs.get('terminal_id'))
        except Exception as e:
            _logger.error(f"Terminal test endpoint error: {e}")
            return {'success': False, 'error': str(e)}