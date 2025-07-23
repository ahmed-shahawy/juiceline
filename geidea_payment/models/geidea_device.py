from odoo import models, fields

class GeideaDevice(models.Model):
    _name = "geidea.device"
    _description = "Geidea Payment Terminal"

    name = fields.Char(string="اسم الجهاز", required=True)
    ip_address = fields.Char(string="عنوان IP")
    location = fields.Char(string="الموقع (اختياري)")
    active = fields.Boolean(default=True)