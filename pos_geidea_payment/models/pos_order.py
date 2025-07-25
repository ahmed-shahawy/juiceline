# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Geidea payment transactions
    geidea_payment_ids = fields.One2many(
        'geidea.payment',
        'pos_order_id',
        string="Geidea Payments",
        help="Geidea payment transactions for this order"
    )
    
    has_geidea_payment = fields.Boolean(
        string="Has Geidea Payment",
        compute='_compute_has_geidea_payment',
        store=True,
        help="Whether this order has Geidea payments"
    )
    
    geidea_total_amount = fields.Monetary(
        string="Geidea Total Amount",
        compute='_compute_geidea_totals',
        store=True,
        help="Total amount paid through Geidea"
    )
    
    geidea_refunded_amount = fields.Monetary(
        string="Geidea Refunded Amount",
        compute='_compute_geidea_totals',
        store=True,
        help="Total amount refunded through Geidea"
    )
    
    @api.depends('geidea_payment_ids')
    def _compute_has_geidea_payment(self):
        for order in self:
            order.has_geidea_payment = bool(order.geidea_payment_ids)
    
    @api.depends('geidea_payment_ids.amount', 'geidea_payment_ids.state')
    def _compute_geidea_totals(self):
        for order in self:
            completed_payments = order.geidea_payment_ids.filtered(
                lambda p: p.state == 'completed' and not p.original_transaction_id
            )
            refund_payments = order.geidea_payment_ids.filtered(
                lambda p: p.state == 'completed' and p.original_transaction_id
            )
            
            order.geidea_total_amount = sum(completed_payments.mapped('amount'))
            order.geidea_refunded_amount = abs(sum(refund_payments.mapped('amount')))
    
    def create_geidea_payment(self, payment_data):
        """Create a new Geidea payment transaction for this order"""
        self.ensure_one()
        
        # Prepare payment data
        payment_vals = {
            'pos_order_id': self.id,
            'pos_session_id': self.session_id.id,
            'currency_id': self.currency_id.id,
            'reference': f"Order {self.name}",
            **payment_data
        }
        
        # Create the payment record
        payment = self.env['geidea.payment'].create(payment_vals)
        
        return payment
    
    def action_refund_geidea_payments(self):
        """Action to refund all Geidea payments for this order"""
        self.ensure_one()
        
        if not self.has_geidea_payment:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("No Geidea Payments"),
                    'message': _("This order has no Geidea payments to refund"),
                    'type': 'warning'
                }
            }
        
        completed_payments = self.geidea_payment_ids.filtered(
            lambda p: p.state == 'completed' and not p.original_transaction_id
        )
        
        if not completed_payments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("No Refundable Payments"),
                    'message': _("This order has no completed Geidea payments to refund"),
                    'type': 'warning'
                }
            }
        
        # Create wizard for refund selection
        return {
            'type': 'ir.actions.act_window',
            'name': _("Refund Geidea Payments"),
            'res_model': 'geidea.payment.refund.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_payment_ids': [(6, 0, completed_payments.ids)],
            }
        }