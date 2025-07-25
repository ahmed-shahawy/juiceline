# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Existing field
    bonat_discount_percentage_product_id = fields.Many2one(
        'product.product',
        string="Bonat Discount Product",
        help="This product will be used as down payment on a sale order."
    )
    
    # Enhanced payment method support
    enable_loyalty_payments = fields.Boolean(
        string="Enable Loyalty Points Payment",
        default=False,
        help="Allow customers to pay using loyalty points"
    )
    
    loyalty_points_conversion_rate = fields.Float(
        string="Loyalty Points Conversion Rate",
        default=1.0,
        help="1 loyalty point = X currency units"
    )
    
    enable_gift_card_payments = fields.Boolean(
        string="Enable Gift Card Payments",
        default=False,
        help="Allow customers to pay using gift cards"
    )
    
    enable_wallet_payments = fields.Boolean(
        string="Enable Digital Wallet Payments",
        default=False,
        help="Enable digital wallet payment methods"
    )
    
    # Cash rounding enhancements
    enable_smart_rounding = fields.Boolean(
        string="Enable Smart Cash Rounding",
        default=False,
        help="Automatically apply optimal cash rounding based on payment method"
    )
    
    rounding_threshold = fields.Float(
        string="Rounding Threshold",
        default=0.02,
        help="Maximum amount difference for automatic rounding"
    )
    
    # Transaction limits for security
    max_discount_percentage = fields.Float(
        string="Maximum Discount Percentage",
        default=50.0,
        help="Maximum discount percentage that can be applied"
    )
    
    max_transaction_amount = fields.Float(
        string="Maximum Transaction Amount",
        default=10000.0,
        help="Maximum amount for a single transaction"
    )
    
    require_manager_approval_amount = fields.Float(
        string="Manager Approval Required Above",
        default=1000.0,
        help="Transactions above this amount require manager approval"
    )

    @api.constrains('loyalty_points_conversion_rate')
    def _check_loyalty_conversion_rate(self):
        for record in self:
            if record.loyalty_points_conversion_rate <= 0:
                raise ValidationError(_("Loyalty points conversion rate must be positive."))

    @api.constrains('max_discount_percentage')
    def _check_max_discount_percentage(self):
        for record in self:
            if record.max_discount_percentage < 0 or record.max_discount_percentage > 100:
                raise ValidationError(_("Maximum discount percentage must be between 0 and 100."))

    @api.constrains('max_transaction_amount')
    def _check_max_transaction_amount(self):
        for record in self:
            if record.max_transaction_amount <= 0:
                raise ValidationError(_("Maximum transaction amount must be positive."))

    @api.constrains('rounding_threshold')
    def _check_rounding_threshold(self):
        for record in self:
            if record.rounding_threshold < 0 or record.rounding_threshold > 1:
                raise ValidationError(_("Rounding threshold must be between 0 and 1."))

    @api.model
    def _load_pos_data_fields(self, config_id):
        return super()._load_pos_data_fields(config_id) + [
            "enable_loyalty_payments",
            "loyalty_points_conversion_rate", 
            "enable_gift_card_payments",
            "enable_wallet_payments",
            "enable_smart_rounding",
            "rounding_threshold",
            "max_discount_percentage",
            "max_transaction_amount",
            "require_manager_approval_amount"
        ]
