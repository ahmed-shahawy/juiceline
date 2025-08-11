# Installation and Usage Guide
# دليل التركيب والاستخدام

## Installation / التركيب

### Prerequisites / المتطلبات
- Odoo 18.0 or higher
- Access to Odoo Apps/Modules management
- Purchase module enabled

### Installation Steps / خطوات التركيب

1. **Copy Module / نسخ المديول**
   ```bash
   cp -r supplier_unit_measurement /path/to/odoo/addons/
   ```

2. **Update Apps List / تحديث قائمة التطبيقات**
   - Go to Apps → Update Apps List
   - انتقل إلى التطبيقات ← تحديث قائمة التطبيقات

3. **Install Module / تركيب المديول**
   - Search for "مديول تحديد وحدة قياس الشراء للموردين"
   - Click Install
   - ابحث عن "مديول تحديد وحدة قياس الشراء للموردين"
   - اضغط تركيب

## Configuration / الإعداد

### Step 1: Setup Suppliers / الخطوة 1: إعداد الموردين

1. Navigate to Contacts → Suppliers
   انتقل إلى جهات الاتصال ← الموردين

2. Open a supplier record
   افتح سجل مورد

3. Go to "وحدات القياس" (UOM) tab
   انتقل إلى تبويب "وحدات القياس"

4. Add supplier unit measurements:
   أضف وحدات قياس المورد:
   - Product / المنتج
   - Supplier UOM / وحدة قياس المورد
   - Standard UOM / الوحدة القياسية
   - Conversion Factor / معامل التحويل

### Step 2: Configure Conversion Rules / الخطوة 2: إعداد قواعد التحويل

1. Go to "وحدات قياس الموردين" → "قواعد التحويل"
   Navigate to "Supplier Unit Measurement" → "Conversion Rules"

2. Create conversion rules between different UOMs
   أنشئ قواعد تحويل بين وحدات القياس المختلفة

## Usage Examples / أمثلة الاستخدام

### Example 1: Basic Supplier UOM Setup / مثال 1: إعداد أساسي لوحدة قياس المورد

**Scenario / السيناريو:**
- Product: Apples / التفاح
- Supplier A: Uses Kilograms / يستخدم الكيلوجرام
- Supplier B: Uses Pounds / يستخدم الباوند

**Configuration / الإعداد:**

Supplier A:
- Product: Apples
- Supplier UOM: Kilogram
- Standard UOM: Kilogram
- Conversion Factor: 1.0

Supplier B:
- Product: Apples
- Supplier UOM: Pound
- Standard UOM: Kilogram  
- Conversion Factor: 0.453592

### Example 2: Using the API / مثال 2: استخدام واجهة البرمجة

**Convert Quantity / تحويل الكمية:**
```javascript
// Convert 10 kg to pounds
fetch('/api/supplier_uom/convert', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        quantity: 10,
        from_uom_id: 1, // Kilogram
        to_uom_id: 2    // Pound
    })
});
```

**Get Supplier UOM / الحصول على وحدة قياس المورد:**
```javascript
fetch('/api/supplier_uom/get_supplier_uom', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        partner_id: 1,      // Supplier ID
        product_tmpl_id: 1  // Product Template ID
    })
});
```

### Example 3: Python Usage / مثال 3: الاستخدام في Python

```python
# In Odoo model methods
def convert_supplier_quantities(self):
    # Get conversion service
    supplier_uom_obj = self.env['supplier.uom']
    
    # Convert quantity between suppliers
    converted_qty = supplier_uom_obj.convert_quantity(
        quantity=100,
        from_partner_id=self.supplier_a.id,
        to_partner_id=self.supplier_b.id,
        product_tmpl_id=self.product.id
    )
    
    return converted_qty
```

## Features / الميزات

### Core Features / الميزات الأساسية

1. **Multi-Supplier UOM Management / إدارة وحدات قياس متعددة الموردين**
   - Define different units for each supplier
   - تحديد وحدات مختلفة لكل مورد

2. **Automatic Conversion / التحويل التلقائي**
   - Convert between different units automatically
   - تحويل بين الوحدات المختلفة تلقائياً

3. **API Integration / تكامل واجهة البرمجة**
   - RESTful APIs for external integration
   - واجهات برمجية للتكامل الخارجي

4. **User-Friendly Interface / واجهة سهلة الاستخدام**
   - Intuitive forms and views
   - نماذج وعروض بديهية

### Advanced Features / الميزات المتقدمة

1. **Conversion Factor Validation / التحقق من معامل التحويل**
   - Ensures positive conversion factors
   - يضمن معاملات تحويل موجبة

2. **Default UOM Selection / اختيار وحدة القياس الافتراضية**
   - Set default units for each supplier-product combination
   - تحديد وحدات افتراضية لكل مزيج مورد-منتج

3. **Category-Based Conversion / التحويل المبني على الفئة**
   - Validates conversions within same UOM category
   - يتحقق من التحويلات ضمن نفس فئة وحدة القياس

## Troubleshooting / استكشاف الأخطاء

### Common Issues / المشاكل الشائعة

1. **Module Not Appearing / المديول لا يظهر**
   - Check if module is in addons path
   - Update apps list
   - تحقق من وجود المديول في مسار الإضافات
   - حدث قائمة التطبيقات

2. **Conversion Not Working / التحويل لا يعمل**
   - Verify conversion factors are positive
   - Check UOM categories match
   - تحقق من أن معاملات التحويل موجبة
   - تأكد من تطابق فئات وحدات القياس

3. **API Errors / أخطاء واجهة البرمجة**
   - Check authentication
   - Verify request format
   - تحقق من المصادقة
   - تحقق من تنسيق الطلب

## Support / الدعم

For support and questions, please contact:
للدعم والاستفسارات، يرجى التواصل مع:

- Developer: Ahmed Shahawy
- المطور: أحمد شحاتة
- Email: [Contact Information]
- البريد الإلكتروني: [معلومات الاتصال]