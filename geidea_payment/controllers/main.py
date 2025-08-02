# -*- coding: utf-8 -*-

import logging
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class GeideaController(http.Controller):

    @http.route('/payment/geidea/return', type='http', auth='public', csrf=False)
    def geidea_return(self, **kwargs):
        """ Handle return from Geidea payment """
        _logger.info("Geidea payment return with data: %s", kwargs)
        
        # Process the return data
        # This would typically validate the payment and update the transaction
        
        return request.redirect('/payment/status')
    
    @http.route('/payment/geidea/webhook', type='http', auth='public', csrf=False)
    def geidea_webhook(self, **kwargs):
        """ Handle webhooks from Geidea """
        _logger.info("Geidea webhook received with data: %s", kwargs)
        
        # Process webhook data
        # This would typically update transaction status based on webhook notifications
        
        return "OK"