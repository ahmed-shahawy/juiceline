# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json


class SupplierUomController(http.Controller):

    @http.route('/api/supplier_uom/convert', type='json', auth='user', methods=['POST'])
    def convert_quantity(self, quantity, from_uom_id, to_uom_id):
        """
        API endpoint لتحويل الكميات بين وحدات القياس
        """
        try:
            conversion_service = request.env['uom.conversion']
            converted_quantity = conversion_service.convert_quantity(
                float(quantity), int(from_uom_id), int(to_uom_id)
            )
            return {
                'success': True,
                'converted_quantity': converted_quantity,
                'original_quantity': quantity,
                'from_uom_id': from_uom_id,
                'to_uom_id': to_uom_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/supplier_uom/get_supplier_uom', type='json', auth='user', methods=['POST'])
    def get_supplier_uom(self, partner_id, product_tmpl_id):
        """
        API endpoint للحصول على وحدة قياس المورد للمنتج
        """
        try:
            supplier_uom_service = request.env['supplier.uom']
            supplier_uom = supplier_uom_service.get_supplier_uom(
                int(partner_id), int(product_tmpl_id)
            )
            
            if supplier_uom:
                return {
                    'success': True,
                    'supplier_uom': {
                        'id': supplier_uom.id,
                        'supplier_uom_id': supplier_uom.supplier_uom_id.id,
                        'supplier_uom_name': supplier_uom.supplier_uom_id.name,
                        'standard_uom_id': supplier_uom.standard_uom_id.id,
                        'standard_uom_name': supplier_uom.standard_uom_id.name,
                        'conversion_factor': supplier_uom.conversion_factor,
                        'is_default': supplier_uom.is_default
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'لم يتم العثور على وحدة قياس للمورد والمنتج المحددين'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/supplier_uom/convert_supplier_quantity', type='json', auth='user', methods=['POST'])
    def convert_supplier_quantity(self, quantity, from_partner_id, to_partner_id, product_tmpl_id):
        """
        API endpoint لتحويل الكميات بين موردين مختلفين
        """
        try:
            supplier_uom_service = request.env['supplier.uom']
            converted_quantity = supplier_uom_service.convert_quantity(
                float(quantity), int(from_partner_id), int(to_partner_id), int(product_tmpl_id)
            )
            return {
                'success': True,
                'converted_quantity': converted_quantity,
                'original_quantity': quantity,
                'from_partner_id': from_partner_id,
                'to_partner_id': to_partner_id,
                'product_tmpl_id': product_tmpl_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/supplier_uom/conversion_factor', type='json', auth='user', methods=['POST'])
    def get_conversion_factor(self, from_uom_id, to_uom_id):
        """
        API endpoint للحصول على معامل التحويل بين وحدتي قياس
        """
        try:
            conversion_service = request.env['uom.conversion']
            factor = conversion_service.get_conversion_factor(
                int(from_uom_id), int(to_uom_id)
            )
            return {
                'success': True,
                'conversion_factor': factor,
                'from_uom_id': from_uom_id,
                'to_uom_id': to_uom_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }