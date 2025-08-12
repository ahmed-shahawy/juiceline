# Multi UOM Supplier Module

## نظرة عامة (Overview)

وحدة Multi UOM Supplier تتيح لنظام Odoo دعم وحدات قياس متعددة للموردين لنفس المنتج. هذا يحل مشكلة أساسية في Odoo حيث يمكن تعيين وحدة شراء واحدة فقط لكل منتج.

The Multi UOM Supplier module enables Odoo to support multiple units of measure for suppliers for the same product. This solves a fundamental issue in Odoo where only one purchase unit can be assigned per product.

## المميزات (Features)

### 1. وحدات قياس متعددة للموردين (Multiple UOMs per Supplier)
- إضافة حقل "وحدة القياس للمورد" في معلومات المورد
- إمكانية تحديد وحدة قياس مختلفة لكل مورد
- التحقق من صحة وحدات القياس (نفس فئة الوحدة)

### 2. التحويل التلقائي في أوامر الشراء (Automatic Conversion in Purchase Orders)
- استخدام وحدة القياس المحددة للمورد تلقائياً
- تحويل الكميات بين وحدات القياس المختلفة
- حساب الأسعار بشكل صحيح بناء على وحدة القياس

### 3. واجهة مستخدم محسنة (Enhanced User Interface)
- عرض وحدة القياس للمورد في نماذج المنتجات
- إمكانية إدارة وحدات القياس للموردين
- عرض معلومات وحدة القياس في أوامر الشراء

## التثبيت (Installation)

1. انسخ مجلد `multi_uom_supplier` إلى مجلد الوحدات في Odoo
2. أعد تشغيل خادم Odoo
3. ادخل إلى قائمة التطبيقات وابحث عن "Multi UOM Supplier"
4. انقر على "تثبيت"

## الاستخدام (Usage)

### إعداد وحدات القياس للموردين (Setting up Supplier UOMs)

1. اذهب إلى المنتجات → المنتجات
2. افتح منتج موجود أو أنشئ منتج جديد
3. في تبويب "الشراء"، اذهب إلى قسم "معلومات المورد"
4. أضف مورد جديد أو عدّل مورد موجود
5. حدد "وحدة القياس للمورد" المناسبة
6. احفظ التغييرات

### إنشاء أوامر الشراء (Creating Purchase Orders)

عند إنشاء أمر شراء جديد:
1. اختر المورد
2. أضف المنتجات
3. ستُستخدم وحدة القياس المحددة للمورد تلقائياً
4. ستُحوّل الكميات والأسعار بناء على وحدة القياس

## الأمثلة (Examples)

### مثال: منتج بوحدات قياس مختلفة

**المنتج**: زيت الطبخ
**وحدة القياس الأساسية**: لتر

**الموردون**:
- المورد أ: يبيع باللتر (1 لتر = 5 دولار)
- المورد ب: يبيع بالجالون (1 جالون = 18 دولار)
- المورد ج: يبيع بالملليلتر (1000 مل = 5 دولار)

عند إنشاء أمر شراء:
- من المورد أ: 10 لتر
- من المورد ب: 3 جالون (سيُحوّل تلقائياً)
- من المورد ج: 5000 مل (سيُحوّل تلقائياً)

## الهيكل التقني (Technical Structure)

### النماذج المُحدثة (Extended Models)

#### product.supplierinfo
- `supplier_uom`: وحدة القياس المستخدمة من قِبل المورد
- `_get_supplier_uom()`: الحصول على وحدة القياس للمورد
- `_convert_price_to_product_uom()`: تحويل السعر إلى وحدة المنتج
- `_convert_price_from_product_uom()`: تحويل السعر من وحدة المنتج

#### purchase.order.line
- `supplier_uom`: وحدة القياس للمورد (محسوبة)
- `_compute_supplier_uom()`: حساب وحدة القياس للمورد
- `_onchange_product_supplier_uom()`: تحديث الوحدة عند تغيير المنتج/المورد

## الملفات المُنجزة (Completed Files)

```
multi_uom_supplier/
├── __init__.py                    # Module initialization
├── __manifest__.py               # Module manifest with dependencies
├── models/
│   ├── __init__.py              # Models initialization
│   ├── product_supplierinfo.py # Extended supplier info model
│   └── purchase_order_line.py  # Extended purchase order line model
├── views/
│   └── product_views.xml       # UI enhancements and views
├── security/
│   └── ir.model.access.csv     # Access rights and security
├── data/
│   └── demo_data.xml           # Demo data for testing
└── README.md                   # This documentation
```

### الاختبار (Testing)

تم إنشاء بيانات تجريبية لتسهيل الاختبار:
- منتج: زيت الطبخ
- مورد أ: يبيع باللتر (5 دولار/لتر)
- مورد ب: يبيع بالجالون (18 دولار/جالون)  
- مورد ج: يبيع بالملليلتر (0.005 دولار/مل)

Demo data has been created for easy testing:
- Product: Cooking Oil
- Supplier A: Sells in Liters (5$/L)
- Supplier B: Sells in Gallons (18$/Gal)
- Supplier C: Sells in Milliliters (0.005$/mL)

## المتطلبات (Requirements)

- Odoo 18.0+
- الوحدات المطلوبة:
  - `purchase` (الشراء)
  - `product` (المنتجات)
  - `uom` (وحدات القياس)

## المساهمة (Contributing)

لتقديم مساهمات أو الإبلاغ عن مشاكل، يرجى:
1. إنشاء issue في المستودع
2. وصف المشكلة أو التحسين المطلوب
3. تقديم pull request مع التغييرات

## الرخصة (License)

هذه الوحدة مرخصة تحت رخصة LGPL-3.

## الدعم (Support)

للحصول على الدعم:
- راجع هذا الدليل أولاً
- ابحث في القضايا الموجودة
- أنشئ قضية جديدة إذا لم تجد حلاً

---

## Technical Implementation Details

### UOM Conversion Logic

The module implements intelligent UOM conversion:

1. **Supplier UOM Validation**: Ensures supplier UOM belongs to the same category as product's purchase UOM
2. **Price Conversion**: Automatically converts prices between different UOMs
3. **Quantity Conversion**: Handles quantity conversion in purchase orders
4. **Procurement Integration**: Works with Odoo's procurement system

### Database Schema Changes

The module adds the following field:
- `product_supplierinfo.supplier_uom` (Many2one to uom.uom)

### View Modifications

- Product forms: Show supplier UOM in supplier info
- Purchase order forms: Display supplier UOM information
- Supplier info forms: Enhanced UOM management

This module maintains full compatibility with existing Odoo functionality while adding the multi-UOM supplier capability.