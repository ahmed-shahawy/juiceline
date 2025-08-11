# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UomConversion(models.Model):
    _name = 'uom.conversion'
    _description = 'Unit of Measure Conversion Rules'
    _rec_name = 'display_name'

    name = fields.Char(string='اسم قاعدة التحويل', required=True)
    from_uom_id = fields.Many2one('uom.uom', string='من وحدة', required=True)
    to_uom_id = fields.Many2one('uom.uom', string='إلى وحدة', required=True)
    factor = fields.Float(
        string='معامل التحويل',
        required=True,
        default=1.0,
        help='للتحويل من الوحدة الأولى إلى الوحدة الثانية، اضرب في هذا المعامل'
    )
    category_id = fields.Many2one(
        'uom.category',
        string='فئة وحدة القياس',
        help='فئة وحدة القياس للتحقق من صحة التحويل'
    )
    active = fields.Boolean(string='نشط', default=True)
    display_name = fields.Char(
        string='اسم العرض',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('from_uom_id.name', 'to_uom_id.name', 'factor')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"1 {record.from_uom_id.name} = {record.factor} {record.to_uom_id.name}"

    @api.constrains('factor')
    def _check_factor(self):
        for record in self:
            if record.factor <= 0:
                raise ValidationError(_('معامل التحويل يجب أن يكون أكبر من الصفر'))

    @api.constrains('from_uom_id', 'to_uom_id')
    def _check_uom_category(self):
        for record in self:
            if record.from_uom_id.category_id != record.to_uom_id.category_id:
                raise ValidationError(_('لا يمكن التحويل بين وحدات قياس من فئات مختلفة'))

    @api.model
    def get_conversion_factor(self, from_uom_id, to_uom_id):
        """الحصول على معامل التحويل بين وحدتي قياس"""
        if from_uom_id == to_uom_id:
            return 1.0
        
        # البحث عن قاعدة تحويل مباشرة
        conversion = self.search([
            ('from_uom_id', '=', from_uom_id),
            ('to_uom_id', '=', to_uom_id),
            ('active', '=', True)
        ], limit=1)
        
        if conversion:
            return conversion.factor
        
        # البحث عن قاعدة تحويل عكسية
        reverse_conversion = self.search([
            ('from_uom_id', '=', to_uom_id),
            ('to_uom_id', '=', from_uom_id),
            ('active', '=', True)
        ], limit=1)
        
        if reverse_conversion:
            return 1.0 / reverse_conversion.factor
        
        # استخدام آلية التحويل الافتراضية في Odoo
        from_uom = self.env['uom.uom'].browse(from_uom_id)
        to_uom = self.env['uom.uom'].browse(to_uom_id)
        
        if from_uom.category_id == to_uom.category_id:
            return from_uom._compute_quantity(1.0, to_uom)
        
        return 1.0

    @api.model
    def convert_quantity(self, quantity, from_uom_id, to_uom_id):
        """تحويل كمية من وحدة قياس إلى أخرى"""
        factor = self.get_conversion_factor(from_uom_id, to_uom_id)
        return quantity * factor