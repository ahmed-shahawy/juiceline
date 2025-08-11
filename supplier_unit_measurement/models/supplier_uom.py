# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SupplierUom(models.Model):
    _name = 'supplier.uom'
    _description = 'Supplier Unit of Measure'
    _rec_name = 'display_name'

    partner_id = fields.Many2one(
        'res.partner', 
        string='المورد',
        required=True,
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)]
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='المنتج',
        required=True
    )
    supplier_uom_id = fields.Many2one(
        'uom.uom',
        string='وحدة قياس المورد',
        required=True
    )
    standard_uom_id = fields.Many2one(
        'uom.uom',
        string='الوحدة القياسية',
        required=True
    )
    conversion_factor = fields.Float(
        string='معامل التحويل',
        required=True,
        default=1.0,
        help='كم من الوحدة القياسية يساوي وحدة واحدة من وحدة المورد'
    )
    is_default = fields.Boolean(
        string='افتراضي',
        default=False,
        help='هل هذه هي وحدة القياس الافتراضية لهذا المورد والمنتج'
    )
    display_name = fields.Char(
        string='اسم العرض',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('partner_id.name', 'product_tmpl_id.name', 'supplier_uom_id.name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.partner_id.name} - {record.product_tmpl_id.name} ({record.supplier_uom_id.name})"

    @api.constrains('conversion_factor')
    def _check_conversion_factor(self):
        for record in self:
            if record.conversion_factor <= 0:
                raise ValidationError(_('معامل التحويل يجب أن يكون أكبر من الصفر'))

    @api.constrains('partner_id', 'product_tmpl_id', 'supplier_uom_id')
    def _check_unique_supplier_product_uom(self):
        for record in self:
            existing = self.search([
                ('partner_id', '=', record.partner_id.id),
                ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ('supplier_uom_id', '=', record.supplier_uom_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('يوجد بالفعل تكوين لنفس المورد والمنتج ووحدة القياس'))

    @api.model
    def get_supplier_uom(self, partner_id, product_tmpl_id):
        """الحصول على وحدة قياس المورد للمنتج المحدد"""
        supplier_uom = self.search([
            ('partner_id', '=', partner_id),
            ('product_tmpl_id', '=', product_tmpl_id),
            ('is_default', '=', True)
        ], limit=1)
        
        if not supplier_uom:
            supplier_uom = self.search([
                ('partner_id', '=', partner_id),
                ('product_tmpl_id', '=', product_tmpl_id)
            ], limit=1)
        
        return supplier_uom

    @api.model
    def convert_quantity(self, quantity, from_partner_id, to_partner_id, product_tmpl_id):
        """تحويل الكمية من وحدة قياس مورد إلى وحدة قياس مورد آخر"""
        from_supplier_uom = self.get_supplier_uom(from_partner_id, product_tmpl_id)
        to_supplier_uom = self.get_supplier_uom(to_partner_id, product_tmpl_id)
        
        if not from_supplier_uom or not to_supplier_uom:
            return quantity
        
        # تحويل إلى الوحدة القياسية أولاً
        standard_quantity = quantity * from_supplier_uom.conversion_factor
        
        # ثم تحويل إلى وحدة المورد المطلوبة
        converted_quantity = standard_quantity / to_supplier_uom.conversion_factor
        
        return converted_quantity