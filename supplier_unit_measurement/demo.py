#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for Supplier Unit Measurement Module
مثال على استخدام مديول وحدات قياس الموردين

This script demonstrates how the module would work in a real Odoo environment.
Note: This is a simulation since we don't have a running Odoo instance.
"""

class MockRecord:
    """محاكاة سجل Odoo"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockEnv:
    """محاكاة بيئة Odoo"""
    def __init__(self):
        self.suppliers = [
            MockRecord(id=1, name="مورد الفواكه المحلي"),
            MockRecord(id=2, name="مورد الخضروات الدولي"),
        ]
        
        self.products = [
            MockRecord(id=1, name="تفاح"),
            MockRecord(id=2, name="برتقال"),
        ]
        
        self.uoms = [
            MockRecord(id=1, name="كيلوجرام"),
            MockRecord(id=2, name="جرام"),
            MockRecord(id=3, name="باوند"),
            MockRecord(id=4, name="صندوق"),
        ]

def demo_supplier_uom_functionality():
    """عرض توضيحي لوظائف وحدات قياس الموردين"""
    print("=" * 60)
    print("مديول تحديد وحدة قياس الشراء للموردين - عرض توضيحي")
    print("=" * 60)
    
    env = MockEnv()
    
    # محاكاة إعدادات وحدات قياس الموردين
    supplier_uom_configs = [
        {
            'supplier': env.suppliers[0],  # مورد الفواكه المحلي
            'product': env.products[0],    # تفاح
            'supplier_uom': env.uoms[0],   # كيلوجرام
            'standard_uom': env.uoms[0],   # كيلوجرام
            'conversion_factor': 1.0,
            'is_default': True
        },
        {
            'supplier': env.suppliers[1],  # مورد الخضروات الدولي
            'product': env.products[0],    # تفاح
            'supplier_uom': env.uoms[2],   # باوند
            'standard_uom': env.uoms[0],   # كيلوجرام
            'conversion_factor': 0.453592, # 1 باوند = 0.453592 كيلوجرام
            'is_default': True
        },
        {
            'supplier': env.suppliers[0],  # مورد الفواكه المحلي
            'product': env.products[1],    # برتقال
            'supplier_uom': env.uoms[3],   # صندوق
            'standard_uom': env.uoms[0],   # كيلوجرام
            'conversion_factor': 5.0,      # صندوق واحد = 5 كيلوجرام
            'is_default': True
        }
    ]
    
    print("\n1. إعدادات وحدات قياس الموردين:")
    print("-" * 40)
    for config in supplier_uom_configs:
        print(f"المورد: {config['supplier'].name}")
        print(f"المنتج: {config['product'].name}")
        print(f"وحدة المورد: {config['supplier_uom'].name}")
        print(f"معامل التحويل: {config['conversion_factor']}")
        print()
    
    # محاكاة تحويل الكميات
    print("2. أمثلة على تحويل الكميات:")
    print("-" * 40)
    
    # مثال 1: تحويل من كيلوجرام إلى باوند
    kg_quantity = 10  # 10 كيلوجرام
    pound_quantity = kg_quantity / 0.453592  # تحويل إلى باوند
    print(f"تحويل {kg_quantity} كيلوجرام إلى باوند: {pound_quantity:.2f} باوند")
    
    # مثال 2: تحويل من صندوق إلى كيلوجرام
    box_quantity = 3  # 3 صناديق
    kg_from_boxes = box_quantity * 5  # كل صندوق = 5 كيلوجرام
    print(f"تحويل {box_quantity} صناديق إلى كيلوجرام: {kg_from_boxes} كيلوجرام")
    
    # مثال 3: تحويل بين موردين مختلفين
    supplier1_quantity = 20  # 20 كيلوجرام من المورد الأول
    supplier2_quantity = supplier1_quantity / 0.453592  # تحويل لوحدة المورد الثاني (باوند)
    print(f"تحويل {supplier1_quantity} كيلوجرام (مورد 1) إلى وحدة المورد 2: {supplier2_quantity:.2f} باوند")
    
    print("\n3. فوائد استخدام المديول:")
    print("-" * 40)
    benefits = [
        "تحويل تلقائي بين وحدات القياس المختلفة",
        "مقارنة دقيقة للأسعار بين الموردين",
        "تجنب الأخطاء في حساب الكميات",
        "توحيد عملية الشراء والمخزون",
        "مرونة في التعامل مع موردين مختلفين",
        "تقارير دقيقة للمشتريات والمخزون"
    ]
    
    for i, benefit in enumerate(benefits, 1):
        print(f"{i}. {benefit}")
    
    print("\n4. واجهة برمجية (API) للتحويل:")
    print("-" * 40)
    api_examples = [
        "POST /api/supplier_uom/convert - تحويل بين وحدات القياس",
        "POST /api/supplier_uom/get_supplier_uom - الحصول على وحدة قياس المورد",
        "POST /api/supplier_uom/convert_supplier_quantity - تحويل بين موردين",
        "POST /api/supplier_uom/conversion_factor - الحصول على معامل التحويل"
    ]
    
    for api in api_examples:
        print(f"• {api}")
    
    print("\n" + "=" * 60)
    print("انتهى العرض التوضيحي")
    print("=" * 60)

if __name__ == "__main__":
    demo_supplier_uom_functionality()