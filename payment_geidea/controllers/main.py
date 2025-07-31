# -*- coding: utf-8 -*-

import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):
    _return_url = '/payment/geidea/return'
    _webhook_url = '/payment/geidea/webhook'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def geidea_return_from_checkout(self, **data):
        """ Process the return from Geidea checkout. """
        _logger.info("Geidea return data:\n%s", pprint.pformat(data))
        
        # Process the return data
        request.env['payment.transaction'].sudo()._handle_notification_data('geidea', data)
        
        # Redirect to the appropriate page
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def geidea_webhook(self, **data):
        """ Process webhook notifications from Geidea. """
        _logger.info("Geidea webhook data:\n%s", pprint.pformat(data))
        
        # Process the webhook data
        request.env['payment.transaction'].sudo()._handle_notification_data('geidea', data)
        
        return "OK"