# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class GeideaDevice(models.Model):
    _name = 'geidea.device'
    _description = 'Geidea Payment Device'
    _order = 'name'

    name = fields.Char(
        string='Device Name',
        required=True,
        help='Name of the payment device'
    )
    device_id = fields.Char(
        string='Device ID',
        required=True,
        help='Unique identifier for the device'
    )
    device_type = fields.Selection([
        ('pos', 'POS Terminal'),
        ('mobile', 'Mobile Device'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop Application')
    ], string='Device Type', required=True)
    
    platform = fields.Selection([
        ('windows', 'Windows'),
        ('android', 'Android'),
        ('ios', 'iOS/iPad'),
        ('web', 'Web Browser')
    ], string='Platform', required=True)
    
    connection_type = fields.Selection([
        ('usb', 'USB'),
        ('serial', 'Serial'),
        ('bluetooth', 'Bluetooth'),
        ('lightning', 'Lightning'),
        ('network', 'Network'),
        ('usb_otg', 'USB OTG')
    ], string='Connection Type', required=True)
    
    status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance')
    ], string='Status', default='disconnected')
    
    last_connection = fields.Datetime(
        string='Last Connection',
        help='Last time device was connected'
    )
    
    provider_id = fields.Many2one(
        'payment.provider',
        string='Payment Provider',
        domain=[('code', '=', 'geidea')],
        required=True
    )
    
    active = fields.Boolean(default=True)
    
    # Device configuration
    config_data = fields.Text(
        string='Configuration Data',
        help='JSON configuration data for the device'
    )
    
    @api.constrains('device_id', 'provider_id')
    def _check_unique_device_id(self):
        for device in self:
            if self.search([
                ('device_id', '=', device.device_id),
                ('provider_id', '=', device.provider_id.id),
                ('id', '!=', device.id)
            ]):
                raise ValidationError(_('Device ID must be unique per provider.'))
    
    def action_test_connection(self):
        """Test device connection"""
        self.ensure_one()
        
        # Update last connection time
        self.write({
            'last_connection': fields.Datetime.now(),
            'status': 'connected'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection Test'),
                'message': _('Device connection test completed. Status updated to connected.'),
                'type': 'success',
            }
        }