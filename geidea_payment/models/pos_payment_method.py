# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    use_geidea = fields.Boolean(
        string='Use Geidea Payment',
        help='Enable Geidea payment gateway integration'
    )
    geidea_merchant_id = fields.Char(
        string='Geidea Merchant ID',
        help='Merchant ID provided by Geidea'
    )
    geidea_terminal_id = fields.Char(
        string='Geidea Terminal ID',
        help='Terminal ID provided by Geidea'
    )
    geidea_api_key = fields.Char(
        string='Geidea API Key',
        help='API Key for Geidea integration'
    )
    geidea_test_mode = fields.Boolean(
        string='Test Mode',
        default=True,
        help='Enable test mode for Geidea payments'
    )

    @api.constrains('use_geidea', 'geidea_merchant_id', 'geidea_terminal_id')
    def _check_geidea_required_fields(self):
        for record in self:
            if record.use_geidea:
                if not record.geidea_merchant_id:
                    raise ValidationError(_('Geidea Merchant ID is required when Geidea payment is enabled.'))
                if not record.geidea_terminal_id:
                    raise ValidationError(_('Geidea Terminal ID is required when Geidea payment is enabled.'))

    @api.onchange('use_geidea')
    def _onchange_use_geidea(self):
        if self.use_geidea:
            self.is_cash_count = False
            if not self.name:
                self.name = 'Geidea Payment'

    def geidea_payment_request(self, order_amount, order_reference):
        """
        Simulate Geidea payment request
        In a real implementation, this would make actual API calls to Geidea
        """
        self.ensure_one()
        if not self.use_geidea:
            return {'error': 'Geidea payment not enabled for this method'}
        
        # Simulate payment processing
        import random
        import time
        
        # Simulate processing delay
        time.sleep(1)
        
        # Simulate success/failure (90% success rate for demo)
        success = random.random() > 0.1
        
        if success:
            transaction_id = f"GDA{int(time.time())}{random.randint(1000, 9999)}"
            return {
                'success': True,
                'transaction_id': transaction_id,
                'amount': order_amount,
                'reference': order_reference,
                'message': 'Payment processed successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Payment declined by Geidea',
                'message': 'Transaction failed. Please try again or use a different payment method.'
            }