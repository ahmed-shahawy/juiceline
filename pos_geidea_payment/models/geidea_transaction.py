from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class GeideaTransaction(models.Model):
    _name = 'geidea.transaction'
    _description = 'Geidea Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Reference', required=True, readonly=True, default='New')
    date = fields.Datetime('Transaction Date', required=True, default=fields.Datetime.now)
    terminal_id = fields.Many2one('geidea.terminal', string='Terminal', required=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    pos_session_id = fields.Many2one('pos.session', string='POS Session')
    
    amount = fields.Float('Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    
    transaction_type = fields.Selection([
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('void', 'Void')
    ], required=True, default='sale')
    
    geidea_reference = fields.Char('Geidea Reference')
    card_type = fields.Char('Card Type')
    card_number = fields.Char('Card Number (Last 4)')
    approval_code = fields.Char('Approval Code')
    response_code = fields.Char('Response Code')
    response_message = fields.Text('Response Message')
    
    customer_id = fields.Many2one('res.partner', string='Customer')
    customer_email = fields.Char('Customer Email')
    customer_phone = fields.Char('Customer Phone')
    
    is_test_mode = fields.Boolean('Test Mode')
    retry_count = fields.Integer('Retry Count', default=0)
    
    def _get_last_sequence(self):
        return self.search([], order='name desc', limit=1).name
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('geidea.transaction')
        return super().create(vals_list)
    
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft transactions can be confirmed.'))
            
        try:
            # Process payment through Geidea API
            response = self._process_payment()
            
            if response.get('success'):
                self.write({
                    'state': 'completed',
                    'geidea_reference': response.get('reference'),
                    'approval_code': response.get('approval_code'),
                    'response_code': response.get('response_code'),
                    'response_message': response.get('message')
                })
                self._notify_success()
            else:
                self.write({
                    'state': 'failed',
                    'response_code': response.get('error_code'),
                    'response_message': response.get('error_message')
                })
                self._notify_failure()
                
        except Exception as e:
            self.write({
                'state': 'failed',
                'response_message': str(e)
            })
            self._notify_failure()
    
    def _process_payment(self):
        # Implementation of payment processing logic
        terminal = self.terminal_id
        headers = {
            'Authorization': f"Bearer {terminal._decrypt_sensitive_data(terminal.api_key)}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'merchantId': terminal.merchant_id,
            'terminalId': terminal.terminal_id,
            'orderId': self.name,
            'customerEmail': self.customer_email,
            'customerPhone': self.customer_phone,
            'isTest': self.is_test_mode,
        }
        
        # Add implementation for API call
        return {'success': True, 'reference': 'TEST123'}
    
    def _notify_success(self):
        if self.pos_order_id:
            self.env['bus.bus']._sendone(
                f'pos_config_{self.pos_session_id.config_id.id}',
                'GEIDEA_PAYMENT_SUCCESS',
                {
                    'order_id': self.pos_order_id.id,
                    'amount': self.amount,
                    'reference': self.name
                }
            )
    
    def _notify_failure(self):
        if self.pos_order_id:
            self.env['bus.bus']._sendone(
                f'pos_config_{self.pos_session_id.config_id.id}',
                'GEIDEA_PAYMENT_FAILED',
                {
                    'order_id': self.pos_order_id.id,
                    'error': self.response_message
                }
            )