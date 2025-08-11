# مديول تحديد وحدة قياس الشراء للموردين

## وصف المديول

هذا المديول يوفر نظاماً شاملاً لإدارة وحدات القياس المختلفة التي يستخدمها الموردون المختلفون للمنتجات، مما يسهل عملية الشراء والتحويل بين الوحدات.

## الميزات الرئيسية

### 1. إدارة وحدات القياس للموردين
- تحديد وحدات القياس المختلفة لكل مورد
- ربط وحدات القياس بالمنتجات
- تحديد معاملات التحويل بين الوحدات

### 2. تحويل الكميات
- تحويل تلقائي بين وحدات القياس المختلفة
- دعم التحويل بين موردين مختلفين لنفس المنتج
- واجهة برمجية (API) للتحويل

### 3. واجهة مستخدم بديهية
- إدارة وحدات القياس من صفحة المورد
- عرض شامل لجميع وحدات القياس
- حاسبة تحويل تفاعلية

## طريقة الاستخدام

### إعداد وحدات قياس المورد

1. انتقل إلى قائمة "الموردين"
2. اختر المورد المطلوب
3. في تبويب "وحدات القياس"، أضف وحدات القياس المختلفة
4. حدد معامل التحويل لكل وحدة قياس

### استخدام التحويل

```python
# مثال على استخدام خدمة التحويل
converter = self.env['uom.conversion']
converted_qty = converter.convert_quantity(100, from_uom_id, to_uom_id)

# تحويل بين موردين
supplier_uom = self.env['supplier.uom']
converted_qty = supplier_uom.convert_quantity(
    quantity=50,
    from_partner_id=partner1.id,
    to_partner_id=partner2.id,
    product_tmpl_id=product.id
)
```

### استخدام API

```javascript
// تحويل الكمية
fetch('/api/supplier_uom/convert', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        quantity: 100,
        from_uom_id: 1,
        to_uom_id: 2
    })
});

// الحصول على وحدة قياس المورد
fetch('/api/supplier_uom/get_supplier_uom', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        partner_id: 1,
        product_tmpl_id: 1
    })
});
```

## النماذج (Models)

### supplier.uom
- `partner_id`: المورد
- `product_tmpl_id`: المنتج
- `supplier_uom_id`: وحدة قياس المورد
- `standard_uom_id`: الوحدة القياسية
- `conversion_factor`: معامل التحويل
- `is_default`: هل هي الوحدة الافتراضية

### uom.conversion
- `name`: اسم قاعدة التحويل
- `from_uom_id`: وحدة القياس المصدر
- `to_uom_id`: وحدة القياس المطلوبة
- `factor`: معامل التحويل
- `active`: حالة القاعدة

## متطلبات التشغيل

- Odoo 18.0+
- الوحدات المطلوبة: `base`, `purchase`, `uom`

## الترخيص

LGPL-3

## المطور

Ahmed Shahawy