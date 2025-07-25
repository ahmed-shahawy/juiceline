# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Geidea terminal configuration
    geidea_terminal_ids = fields.Many2many(
        'geidea.terminal',
        string='Geidea Terminals',
        help='Geidea payment terminals available for this POS'
    )
    
    geidea_auto_connect = fields.Boolean(
        string='Auto Connect to Geidea Terminals',
        default=True,
        help='Automatically connect to Geidea terminals when POS session starts'
    )
    
    geidea_payment_timeout = fields.Integer(
        string='Payment Timeout (seconds)',
        default=60,
        help='Timeout for Geidea payment transactions'
    )
    
    geidea_receipt_options = fields.Selection([
        ('pos_only', 'POS Receipt Only'),
        ('terminal_only', 'Terminal Receipt Only'),
        ('both', 'Both POS and Terminal Receipts'),
        ('customer_choice', 'Let Customer Choose')
    ], string='Receipt Options', default='both')

    def _get_geidea_terminal_config(self):
        """Get Geidea terminal configuration for POS session"""
        self.ensure_one()
        terminals = []
        for terminal in self.geidea_terminal_ids:
            if terminal.active:
                terminals.append(terminal.get_connection_config())
        
        return {
            'terminals': terminals,
            'auto_connect': self.geidea_auto_connect,
            'payment_timeout': self.geidea_payment_timeout,
            'receipt_options': self.geidea_receipt_options,
        }